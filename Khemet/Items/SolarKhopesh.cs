using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Items
{
    public class SolarKhopesh : ModItem
    {
        public override void SetDefaults()
        {
            Item.width = 44;
            Item.height = 44;
            Item.rare = ItemRarityID.Red;
            Item.value = 500000;
            Item.damage = 152;
            Item.DamageType = DamageClass.Melee;
            Item.useTime = 18;
            Item.useAnimation = 18;
            Item.useStyle = ItemUseStyleID.Swing;
            Item.knockBack = 7.0f;
            Item.UseSound = SoundID.Item1;
            Item.autoReuse = true;
        }

        public override void ModifyHitNPC(Player player, NPC target, ref NPC.HitModifiers modifiers)
        {
            if (target.type == NPCID.Mummy || target.type == NPCID.DarkMummy || target.type == NPCID.LightMummy || target.type == NPCID.Zombie || target.type == NPCID.Skeleton || target.type == NPCID.Ghost || target.type == ModContent.NPCType<NPCs.TombGuardian>())
            {
                modifiers.FinalDamage *= 1.4f;
            }
        }
    }
}
