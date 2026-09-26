(function(){
 const KEY='ashfall_reader_theme';let mode='system';
 try{const v=localStorage.getItem(KEY);if(['system','light','dark'].includes(v))mode=v;}catch(e){}
 const media=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;
 const apply=()=>{const theme=mode==='system'?(media&&media.matches?'dark':'light'):mode;document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme;window.dispatchEvent(new CustomEvent('ashfall-theme-change',{detail:{mode,theme}}));};
 window.AshfallAppearance={getMode:()=>mode,getTheme:()=>document.documentElement.dataset.theme,setMode(v){if(!['system','light','dark'].includes(v))throw Error('invalid theme');mode=v;let persisted=true;try{localStorage.setItem(KEY,v);}catch(e){persisted=false;}apply();return persisted;}};
 if(media){if(media.addEventListener)media.addEventListener('change',()=>{if(mode==='system')apply();});else if(media.addListener)media.addListener(()=>{if(mode==='system')apply();});}
 apply();
})();
