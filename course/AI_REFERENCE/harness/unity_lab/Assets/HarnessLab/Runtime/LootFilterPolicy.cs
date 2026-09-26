using System;
namespace HarnessLab
{
    public enum Rarity { Normal, Magic, Rare }
    public enum Filter { All, MagicPlus, RareOnly }
    public static class LootFilterPolicy
    {
        public static bool Visible(Rarity rarity, Filter mode, bool quest, bool reveal)
        {
            if (quest || reveal) return true;
            if (!Enum.IsDefined(typeof(Rarity), rarity)) return true;
            if (!Enum.IsDefined(typeof(Filter), mode)) return true;
            return mode == Filter.All || (int)rarity >= (int)mode;
        }
    }
}
