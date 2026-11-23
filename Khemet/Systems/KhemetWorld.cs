using System.IO;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Khemet.Systems
{
    /// <summary>World state: which bosses have fallen, and where the Grand Pyramid stands (tile coordinates).</summary>
    public class KhemetWorld : ModSystem
    {
        public static bool downedForgottenPharaoh;
        public static bool downedAnubis;
        public static bool downedSunPharaoh;
        public static Rectangle PyramidArea;

        public static bool InPyramid(Player player)
        {
            return PyramidArea.Width > 0 && PyramidArea.Contains(player.Center.ToTileCoordinates());
        }

        public override void ClearWorld()
        {
            downedForgottenPharaoh = false;
            downedAnubis = false;
            downedSunPharaoh = false;
            PyramidArea = Rectangle.Empty;
        }

        public override void SaveWorldData(TagCompound tag)
        {
            if (downedForgottenPharaoh) { tag["downedForgottenPharaoh"] = true; }
            if (downedAnubis) { tag["downedAnubis"] = true; }
            if (downedSunPharaoh) { tag["downedSunPharaoh"] = true; }
            tag["pyX"] = PyramidArea.X;
            tag["pyY"] = PyramidArea.Y;
            tag["pyW"] = PyramidArea.Width;
            tag["pyH"] = PyramidArea.Height;
        }

        public override void LoadWorldData(TagCompound tag)
        {
            downedForgottenPharaoh = tag.ContainsKey("downedForgottenPharaoh");
            downedAnubis = tag.ContainsKey("downedAnubis");
            downedSunPharaoh = tag.ContainsKey("downedSunPharaoh");
            PyramidArea = new Rectangle(tag.GetInt("pyX"), tag.GetInt("pyY"), tag.GetInt("pyW"), tag.GetInt("pyH"));
        }

        public override void NetSend(BinaryWriter writer)
        {
            writer.Write(downedForgottenPharaoh);
            writer.Write(downedAnubis);
            writer.Write(downedSunPharaoh);
            writer.Write(PyramidArea.X);
            writer.Write(PyramidArea.Y);
            writer.Write(PyramidArea.Width);
            writer.Write(PyramidArea.Height);
        }

        public override void NetReceive(BinaryReader reader)
        {
            downedForgottenPharaoh = reader.ReadBoolean();
            downedAnubis = reader.ReadBoolean();
            downedSunPharaoh = reader.ReadBoolean();
            PyramidArea = new Rectangle(reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32());
        }
    }
}
