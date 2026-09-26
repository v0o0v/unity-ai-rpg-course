"""AI-only bounded quest contract reference, not Unity runtime or Editor code.

No API/network/file-write actions. Import validate_draft and preview_apply in tests.
Only the small teaching schema is supported; a real project must bind its own schema.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
import re

class ContractError(ValueError):
    pass

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)

def obj(value: Any, allowed: set[str], required: set[str], label: str) -> dict:
    require(isinstance(value, dict), label + ': object required')
    require(set(value) <= allowed, label + ': unknown field')
    require(required <= set(value), label + ': missing field')
    return value

def integer(v: Any, lo: int, hi: int, label: str) -> None:
    require(type(v) is int and lo <= v <= hi, label + ': integer out of range')

def ident(v: Any) -> None:
    require(isinstance(v, str) and bool(re.fullmatch(r'[A-Za-z0-9_.-]{1,96}', v)), 'invalid ID')

def validate_draft(draft: dict, registry: dict, *, project_id='GrayOathRPG3D', quest_id='H01', node_limit=16) -> dict:
    """Pure validation; raises ContractError. Returns counts, not a gameplay PASS."""
    integer(node_limit, 1, 128, 'node limit')
    d=obj(draft, {'schemaVersion','projectId','questId','requestId','baseRevision','title','startNode','nodes','edges','declaredRefs','needsContent','note'},
          {'schemaVersion','projectId','questId','requestId','baseRevision','title','startNode','nodes','edges','declaredRefs','needsContent'}, 'draft')
    integer(d['schemaVersion'],1,1,'schema'); integer(d['baseRevision'],0,2**31-1,'revision')
    require(d['projectId']==project_id and d['questId']==quest_id, 'wrong project/quest')
    for k in ('projectId','questId','requestId','startNode'):ident(d[k])
    require(isinstance(d['title'],str) and 0<len(d['title'].strip())<=200, 'title')
    require(isinstance(d['needsContent'],list) and not d['needsContent'], 'missing content: cannot apply')
    allowed_refs={'npc','item','region','target','dialogue','fact','marker','quest'}
    refs=obj(d['declaredRefs'],allowed_refs,set(), 'declaredRefs')
    for kind,ids in refs.items():
        require(isinstance(ids,list) and len(ids)<=1024, 'references list')
        require(all(isinstance(x,str) for x in ids),'reference id type')
        require(len(set(ids))==len(ids),'duplicate declared reference')
        require(set(ids)<=set(registry.get(kind,[])), 'unknown reference: '+kind)
        for x in ids:ident(x)
    def ref(kind: str, v: Any) -> None:
        ident(v)
        require(v in refs.get(kind,[]) and v in registry.get(kind,[]), 'undeclared reference: '+kind)
    def predicate(p: dict, depth=0):
        require(depth<=6,'predicate too deep')
        require(isinstance(p,dict),'predicate object')
        op=p.get('op');require(isinstance(op,str),'predicate op')
        if op in ('All','Any'):
            obj(p,{'op','args'},{'op','args'},'predicate')
            require(isinstance(p['args'],list) and 1<=len(p['args'])<=16,'predicate args')
            for x in p['args']:predicate(x,depth+1)
        elif op=='Not':
            obj(p,{'op','arg'},{'op','arg'},'predicate');predicate(p['arg'],depth+1)
        elif op=='HasItem':
            obj(p,{'op','id','count'},{'op','id','count'},'predicate');ref('item',p['id']);integer(p['count'],1,999,'count')
        elif op=='HasFact':
            obj(p,{'op','id','value'},{'op','id','value'},'predicate');ref('fact',p['id']);require(type(p['value']) is bool,'fact boolean')
        elif op=='QuestState':
            obj(p,{'op','id','state'},{'op','id','state'},'predicate');ref('quest',p['id']);require(p['state'] in ['Locked','Available','Active','Completed','Failed'],'quest state')
        elif op=='LevelAtLeast':
            obj(p,{'op','level'},{'op','level'},'predicate');integer(p['level'],1,20,'level')
        elif op=='TimeWindow':
            obj(p,{'op','start','end'},{'op','start','end'},'predicate');integer(p['start'],0,1439,'start');integer(p['end'],1,1440,'end');require(p['start']<p['end'],'window wrap not supported in this schema')
        else: raise ContractError('unknown predicate')
    def action(a: dict):
        require(isinstance(a,dict),'action object');op=a.get('op');require(isinstance(op,str),'action op')
        if op=='SetFact':
            obj(a,{'op','id','value'},{'op','id','value'},'action');ref('fact',a['id']);require(type(a['value']) is bool,'fact boolean')
        elif op in ('GiveItem','RemoveItem'):
            obj(a,{'op','id','count'},{'op','id','count'},'action');ref('item',a['id']);integer(a['count'],1,999,'count')
        elif op=='GrantXP':
            obj(a,{'op','amount'},{'op','amount'},'action');integer(a['amount'],0,500,'XP')
        elif op in ('StartDialogue','SetMarker'):
            obj(a,{'op','id'},{'op','id'},'action');ref('dialogue' if op=='StartDialogue' else 'marker',a['id'])
        else:raise ContractError('unknown action')
    require(isinstance(d['nodes'],list) and 1<=len(d['nodes'])<=node_limit,'nodes limit')
    nodes={}; ports={}
    for n in d['nodes']:
        obj(n,{'id','type','data'},{'id','type','data'},'node');ident(n['id']);require(n['id'] not in nodes,'duplicate node')
        typ=n['type'];require(isinstance(typ,str),'node type');data=n['data'];require(isinstance(data,dict),'node data');nodes[n['id']]=n
        if typ=='Start': obj(data,set(),set(),'start');ports[n['id']]={'next'}
        elif typ=='Talk':
            obj(data,{'npc','dialogue'},{'npc','dialogue'},'talk');ref('npc',data['npc']);ref('dialogue',data['dialogue']);ports[n['id']]={'next'}
        elif typ=='Choice':
            obj(data,{'options'},{'options'},'choice');opts=data['options'];require(isinstance(opts,list) and 2<=len(opts)<=8,'options')
            for x in opts:ident(x)
            require(len(set(opts))==len(opts),'duplicate choice option');ports[n['id']]=set(opts)
        elif typ=='Condition':
            obj(data,{'predicate'},{'predicate'},'condition');predicate(data['predicate']);ports[n['id']]={'true','false'}
        elif typ=='Action':
            obj(data,{'actions'},{'actions'},'actions');require(isinstance(data['actions'],list) and 1<=len(data['actions'])<=12,'action count')
            for a in data['actions']:action(a)
            ports[n['id']]={'next'}
        elif typ=='Objective':
            obj(data,{'policy','objectives'},{'policy','objectives'},'objective');require(data['policy'] in ('all','any'),'objective policy')
            require(isinstance(data['objectives'],list) and 1<=len(data['objectives'])<=8,'objective count')
            for o in data['objectives']:
                obj(o,{'kind','target','count','retroactive','proofFact'},{'kind','target','count','retroactive'},'objective part')
                mapping={'Inspect':'target','Collect':'item','Kill':'target','Reach':'region','Escort':'npc','Talk':'npc'}
                require(isinstance(o['kind'],str) and o['kind'] in mapping,'objective kind');ref(mapping[o['kind']],o['target']);integer(o['count'],1,999,'objective count');require(type(o['retroactive']) is bool,'retroactive')
                if 'proofFact' in o:ref('fact',o['proofFact'])
                if o['kind']=='Kill' and o['retroactive']:require('proofFact'in o,'retroactive kill requires explicit proof')
            ports[n['id']]={'completed'}
        elif typ=='Reward':
            obj(data,{'rewardKey','gold','xp'},{'rewardKey','gold','xp'},'reward');ident(data['rewardKey']);integer(data['gold'],0,500,'gold');integer(data['xp'],0,500,'xp');ports[n['id']]={'next'}
        elif typ=='End':
            obj(data,{'result'},{'result'},'end');require(data['result'] in ('Completed','Failed'),'end result');ports[n['id']]=set()
        else:raise ContractError('unknown node type')
    starts=[n['id'] for n in nodes.values() if n['type']=='Start']
    require(starts==[d['startNode']], 'exactly one matching start')
    require(isinstance(d['edges'],list) and len(d['edges'])<=node_limit*8,'edge limit')
    outgoing={x:[] for x in nodes};indegree={x:0 for x in nodes};used=set()
    for e in d['edges']:
        obj(e,{'from','port','to'},{'from','port','to'},'edge')
        a,p,b=e['from'],e['port'],e['to'];ident(a);ident(p);ident(b);require(a in nodes and b in nodes,'missing endpoint');require(p in ports[a],'wrong port')
        require((a,p) not in used,'duplicate port edge');used.add((a,p));outgoing[a].append(b);indegree[b]+=1
    require(indegree[d['startNode']]==0,'start has input')
    for x in nodes:require({p for a,p in used if a==x}==ports[x],'missing outgoing port')
    queue=[x for x,n in indegree.items() if n==0];order=[]
    while queue:
        x=queue.pop(0);order.append(x)
        for y in outgoing[x]:
            indegree[y]-=1
            if indegree[y]==0:queue.append(y)
    require(len(order)==len(nodes),'cycle')
    seen=set();todo=[d['startNode']]
    while todo:
        x=todo.pop()
        if x in seen:continue
        seen.add(x);todo.extend(outgoing[x])
    require(len(seen)==len(nodes),'unreachable nodes')
    terminals={x for x in nodes if nodes[x]['type']=='End'};require(terminals,'no End')
    reaches=set(terminals)
    for x in reversed(order):
        if any(y in reaches for y in outgoing[x]):reaches.add(x)
    require(reaches==set(nodes),'no terminal path')
    rewards=[n['data']['rewardKey'] for n in nodes.values() if n['type']=='Reward'];require(len(rewards)==len(set(rewards)),'duplicate reward key')
    # H01's specification has a fixed single completion reward. Actions cannot
    # bypass that budget with extra XP or generated items. General projects should
    # pass an independently approved budget instead of trusting one in the draft.
    reward_nodes=[n for n in nodes.values() if n['type']=='Reward']
    require(len(reward_nodes)==1,'H01 requires one reward definition')
    require(reward_nodes[0]['data']=={'rewardKey':'H01.completion','gold':80,'xp':120},'H01 reward contract')
    for n in nodes.values():
        if n['type']=='Action':
            require(not any(a['op'] in ('GrantXP','GiveItem') for a in n['data']['actions']),'H01 extra reward action')
    return {'nodes':len(nodes),'edges':len(d['edges']),'structural':'VALID','gameplay':'NOT RUN'}

def preview_apply(draft: dict, registry: dict, *, current_revision: int, approved_request: str | None, cancelled: bool, applied_requests: set[str]) -> dict:
    """Return a copy with the proposed next revision; never modify an asset or input."""
    integer(current_revision,0,2**31-1,'current revision')
    validate_draft(draft,registry)
    require(not cancelled,'cancelled')
    require(draft['requestId']==approved_request,'not approved')
    require(draft['requestId'] not in applied_requests,'already applied')
    require(draft['baseRevision']==current_revision,'stale revision')
    return {'revision':current_revision+1,'requestId':draft['requestId'],'candidate':deepcopy(draft)}

@dataclass
class RewardState:
    gold: int=0
    xp: int=0
    receipts: set[str]=field(default_factory=set)

def reward_transaction(state: RewardState, instance_id: str, reward_key: str, gold: int, xp: int, *, eligible=True) -> RewardState:
    """A pure copy-on-commit model, not disk transaction durability."""
    ident(instance_id);ident(reward_key);integer(gold,0,500,'gold');integer(xp,0,500,'xp')
    require(type(eligible) is bool and eligible,'not eligible')
    key=instance_id+':'+reward_key
    result=deepcopy(state)
    if key in result.receipts:return result
    result.gold+=gold;result.xp+=xp;result.receipts.add(key)
    return result
