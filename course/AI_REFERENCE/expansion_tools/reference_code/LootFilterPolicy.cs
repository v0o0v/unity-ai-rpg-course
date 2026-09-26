// Teaching reference only. Bind to the real game's item model via a small adapter.
// Unity compilation and device execution are NOT RUN in the course production environment.
using System;
namespace Ashfall.Expansion.Reference
{
    public enum LootKind { Equipment = 0, Material = 1, Quest = 2, Gold = 3, Other = 4 }
    public enum LootRarity { Normal = 0, Magic = 1, Rare = 2 }
    public enum LootFilterMode { All = 0, MagicOrBetter = 1, RareOnly = 2 }

    public readonly struct LootLabelInput
    {
        public LootKind Kind { get; }
        public LootRarity Rarity { get; }
        public LootLabelInput(LootKind kind, LootRarity rarity) { Kind = kind; Rarity = rarity; }
    }

    public static class LootFilterPolicy
    {
        // Pure presentation policy: NEVER remove a drop, change ownership, or disable pickup.
        public static bool ShouldShowLabel(LootLabelInput item, LootFilterMode mode, bool revealAll)
        {
            if (revealAll) return true;
            if (item.Kind != LootKind.Equipment) return true;
            if (!Enum.IsDefined(typeof(LootRarity), item.Rarity)) return true;
            switch (mode)
            {
                case LootFilterMode.All: return true;
                case LootFilterMode.MagicOrBetter: return (int)item.Rarity >= (int)LootRarity.Magic;
                case LootFilterMode.RareOnly: return (int)item.Rarity >= (int)LootRarity.Rare;
                default: return true; // Unknown policy: preserve visibility rather than losing loot.
            }
        }
    }
}
