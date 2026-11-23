using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Tiles
{
    public class HieroglyphBrickTile : ModTile
    {
        public override void SetStaticDefaults()
        {
            Main.tileSolid[Type] = true;
            Main.tileMergeDirt[Type] = true;
            Main.tileBlockLight[Type] = true;
            AddMapEntry(new Color(150, 120, 74));
            DustType = DustID.Sand;
            HitSound = SoundID.Tink;
            MineResist = 2.0f;
            MinPick = 0;
        }
    }
}
