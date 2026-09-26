using UnityEngine;
namespace HarnessLab
{
    // Only the label changes; the drop body and pickup collider remain active.
    public sealed class LootLabelView : MonoBehaviour
    {
        [SerializeField] private Rarity rarity;
        [SerializeField] private TextMesh label;
        public void Configure(Rarity value, TextMesh text) { rarity = value; label = text; }
        public void Apply(Filter mode, bool reveal = false)
        {
            if (label != null) label.gameObject.SetActive(LootFilterPolicy.Visible(rarity, mode, false, reveal));
        }
    }
}
