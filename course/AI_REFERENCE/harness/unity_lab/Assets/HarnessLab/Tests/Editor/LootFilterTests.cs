using NUnit.Framework;
namespace HarnessLab.Tests
{
    public class LootFilterTests
    {
        [Test] public void NormalHiddenByRareFilter() => Assert.IsFalse(LootFilterPolicy.Visible(Rarity.Normal, Filter.RareOnly, false, false));
        [Test] public void RareShownByRareFilter() => Assert.IsTrue(LootFilterPolicy.Visible(Rarity.Rare, Filter.RareOnly, false, false));
        [Test] public void QuestAlwaysVisible() => Assert.IsTrue(LootFilterPolicy.Visible(Rarity.Normal, Filter.RareOnly, true, false));
        [Test] public void RevealShowsEverything() => Assert.IsTrue(LootFilterPolicy.Visible(Rarity.Normal, Filter.RareOnly, false, true));
        [Test] public void UnknownModePreservesVisibility() => Assert.IsTrue(LootFilterPolicy.Visible(Rarity.Normal, (Filter)999, false, false));
    }
}
