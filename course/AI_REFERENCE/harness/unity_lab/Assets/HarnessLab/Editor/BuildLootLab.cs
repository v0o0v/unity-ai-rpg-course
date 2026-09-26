using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
namespace HarnessLab.Editor
{
    public static class BuildLootLab
    {
        public static void Build()
        {
            // Run only in the reviewed candidate project, with no unsaved scene open.
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cameraObject = new GameObject("LabCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true; camera.orthographicSize = 4;
            camera.transform.position = new Vector3(0,0,-10);
            var panel = new GameObject("FilterPanel").AddComponent<FilterPanel>();
            panel.labels = new LootLabelView[3];
            for (int i=0; i<3; i++)
            {
                var drop = new GameObject("Drop_" + i);
                drop.transform.position = new Vector3(i*2-2,0,0);
                drop.AddComponent<BoxCollider2D>().size = new Vector2(.8f,.8f);
                var textObject = new GameObject("NameLabel");
                textObject.transform.SetParent(drop.transform, false);
                var text = textObject.AddComponent<TextMesh>();
                text.text = ((Rarity)i).ToString(); text.anchor = TextAnchor.MiddleCenter;
                text.characterSize = .2f; text.fontSize = 32;
                var view = drop.AddComponent<LootLabelView>();
                view.Configure((Rarity)i, text); panel.labels[i] = view;
            }
            Directory.CreateDirectory("Assets/HarnessLab/Scenes");
            if (!EditorSceneManager.SaveScene(scene,"Assets/HarnessLab/Scenes/LootLab.unity"))
                throw new System.InvalidOperationException("Scene save failed");
            AssetDatabase.SaveAssets();
        }
    }
}
