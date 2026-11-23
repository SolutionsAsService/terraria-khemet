using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Items
{
    public class Khopesh : ModItem
    {
        public override void SetDefaults()
        {
            Item.width = 44;
            Item.height = 44;
            Item.rare = ItemRarityID.Orange;
            Item.value = 27000;
            Item.damage = 26;
            Item.DamageType = DamageClass.Melee;
            Item.useTime = 22;
            Item.useAnimation = 22;
            Item.useStyle = ItemUseStyleID.Swing;
            Item.knockBack = 5.0f;
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
