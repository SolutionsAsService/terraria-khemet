using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Tiles
{
    public class LapisInlayTile : ModTile
    {
        public override void SetStaticDefaults()
        {
            Main.tileSolid[Type] = true;
            Main.tileMergeDirt[Type] = true;
            Main.tileBlockLight[Type] = true;
            AddMapEntry(new Color(42, 88, 176));
            DustType = DustID.Stone;
            HitSound = SoundID.Tink;
            MineResist = 3.0f;
            MinPick = 0;
        }
    }
}
