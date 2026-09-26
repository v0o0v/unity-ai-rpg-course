using UnityEngine;
namespace HarnessLab
{
    // IMGUI is isolated lab scaffolding, not the final game's UGUI/mobile interface.
    public sealed class FilterPanel : MonoBehaviour
    {
        public LootLabelView[] labels;
        private void Apply(Filter mode) { foreach (var label in labels) label.Apply(mode); }
        private void OnGUI()
        {
            if (GUI.Button(new Rect(20,20,160,50), "Show all")) Apply(Filter.All);
            if (GUI.Button(new Rect(190,20,160,50), "Rare only")) Apply(Filter.RareOnly);
        }
    }
}
