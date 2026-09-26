// Put in the existing correctly configured EditMode test assembly, NOT arbitrary Assets.
// This file is a reference source, not evidence that Unity has executed these tests.
using NUnit.Framework;
using Ashfall.Expansion.Reference;
namespace Ashfall.Expansion.Tests
{
    public sealed class LootFilterPolicyTests
    {
        private static bool Show(LootKind k, LootRarity r, LootFilterMode m, bool reveal=false)
            => LootFilterPolicy.ShouldShowLabel(new LootLabelInput(k,r),m,reveal);
        [Test] public void AllShowsNormal() => Assert.That(Show(LootKind.Equipment,LootRarity.Normal,LootFilterMode.All),Is.True);
        [Test] public void MagicHidesNormal() => Assert.That(Show(LootKind.Equipment,LootRarity.Normal,LootFilterMode.MagicOrBetter),Is.False);
        [Test] public void MagicShowsMagic() => Assert.That(Show(LootKind.Equipment,LootRarity.Magic,LootFilterMode.MagicOrBetter),Is.True);
        [Test] public void RareHidesMagic() => Assert.That(Show(LootKind.Equipment,LootRarity.Magic,LootFilterMode.RareOnly),Is.False);
        [Test] public void RareShowsRare() => Assert.That(Show(LootKind.Equipment,LootRarity.Rare,LootFilterMode.RareOnly),Is.True);
        [Test] public void RevealOverridesFilter() => Assert.That(Show(LootKind.Equipment,LootRarity.Normal,LootFilterMode.RareOnly,true),Is.True);
        [Test] public void QuestAlwaysVisible() => Assert.That(Show(LootKind.Quest,LootRarity.Normal,LootFilterMode.RareOnly),Is.True);
        [Test] public void MaterialsAlwaysVisible() => Assert.That(Show(LootKind.Material,LootRarity.Normal,LootFilterMode.RareOnly),Is.True);
        [Test] public void GoldAlwaysVisible() => Assert.That(Show(LootKind.Gold,LootRarity.Normal,LootFilterMode.RareOnly),Is.True);
        [Test] public void UnknownKindVisible() => Assert.That(Show((LootKind)999,LootRarity.Normal,LootFilterMode.RareOnly),Is.True);
        [Test] public void UnknownRarityVisible() => Assert.That(Show(LootKind.Equipment,(LootRarity)999,LootFilterMode.RareOnly),Is.True);
        [Test] public void UnknownModeVisible() => Assert.That(Show(LootKind.Equipment,LootRarity.Normal,(LootFilterMode)999),Is.True);
    }
}
