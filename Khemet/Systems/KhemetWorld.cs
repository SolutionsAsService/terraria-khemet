using System.IO;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Khemet.Systems
{
    /// <summary>World state: which bosses have fallen, and where each generated structure stands (tile coordinates).</summary>
    public class KhemetWorld : ModSystem
    {
        public static bool downedForgottenPharaoh;
        public static bool downedAnubis;
        public static bool downedSunPharaoh;
        public static Rectangle GrandPyramidArea;

        public static bool InArea(Player player, Rectangle area)
        {
            return area.Width > 0 && area.Contains(player.Center.ToTileCoordinates());
        }

        public override void ClearWorld()
        {
            downedForgottenPharaoh = false;
            downedAnubis = false;
            downedSunPharaoh = false;
            GrandPyramidArea = Rectangle.Empty;
        }

        public override void SaveWorldData(TagCompound tag)
        {
            if (downedForgottenPharaoh) { tag["downedForgottenPharaoh"] = true; }
            if (downedAnubis) { tag["downedAnubis"] = true; }
            if (downedSunPharaoh) { tag["downedSunPharaoh"] = true; }
            tag["GrandPyramidX"] = GrandPyramidArea.X;
            tag["GrandPyramidY"] = GrandPyramidArea.Y;
            tag["GrandPyramidW"] = GrandPyramidArea.Width;
            tag["GrandPyramidH"] = GrandPyramidArea.Height;
        }

        public override void LoadWorldData(TagCompound tag)
        {
            downedForgottenPharaoh = tag.ContainsKey("downedForgottenPharaoh");
            downedAnubis = tag.ContainsKey("downedAnubis");
            downedSunPharaoh = tag.ContainsKey("downedSunPharaoh");
            GrandPyramidArea = new Rectangle(tag.GetInt("GrandPyramidX"), tag.GetInt("GrandPyramidY"), tag.GetInt("GrandPyramidW"), tag.GetInt("GrandPyramidH"));
        }

        public override void NetSend(BinaryWriter writer)
        {
            writer.Write(downedForgottenPharaoh);
            writer.Write(downedAnubis);
            writer.Write(downedSunPharaoh);
            writer.Write(GrandPyramidArea.X);
            writer.Write(GrandPyramidArea.Y);
            writer.Write(GrandPyramidArea.Width);
            writer.Write(GrandPyramidArea.Height);
        }

        public override void NetReceive(BinaryReader reader)
        {
            downedForgottenPharaoh = reader.ReadBoolean();
            downedAnubis = reader.ReadBoolean();
            downedSunPharaoh = reader.ReadBoolean();
            GrandPyramidArea = new Rectangle(reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32());
        }
    }
}
