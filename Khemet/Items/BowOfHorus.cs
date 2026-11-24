using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Items
{
    public class BowOfHorus : ModItem
    {
        public override void SetDefaults()
        {
            Item.width = 36;
            Item.height = 44;
            Item.rare = ItemRarityID.Lime;
            Item.value = 170000;
            Item.damage = 84;
            Item.DamageType = DamageClass.Ranged;
            Item.useTime = 15;
            Item.useAnimation = 15;
            Item.useStyle = ItemUseStyleID.Shoot;
            Item.noMelee = true;
            Item.knockBack = 4.0f;
            Item.UseSound = SoundID.Item5;
            Item.autoReuse = true;
            Item.shoot = ProjectileID.WoodenArrowFriendly;
            Item.shootSpeed = 17.0f;
            Item.useAmmo = AmmoID.Arrow;
        }
    }
}
