using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Tiles
{
    public class GoldenSandstoneTile : ModTile
    {
        public override void SetStaticDefaults()
        {
            Main.tileSolid[Type] = true;
            Main.tileMergeDirt[Type] = true;
            Main.tileBlockLight[Type] = true;
            AddMapEntry(new Color(232, 190, 60));
            DustType = DustID.Gold;
            HitSound = SoundID.Tink;
            MineResist = 3.0f;
            MinPick = 0;
        }
    }
}
