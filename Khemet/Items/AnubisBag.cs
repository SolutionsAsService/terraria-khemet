using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.Items
{
    public class AnubisBag : ModItem
    {
        public override void SetStaticDefaults()
        {
            ItemID.Sets.BossBag[Type] = true;
            ItemID.Sets.PreHardmodeLikeBossBag[Type] = false;
            Item.ResearchUnlockCount = 3;
        }

        public override void SetDefaults()
        {
            Item.maxStack = Item.CommonMaxStack;
            Item.consumable = true;
            Item.width = 30;
            Item.height = 32;
            Item.rare = ItemRarityID.Expert;
            Item.expert = true;
        }

        public override bool CanRightClick()
        {
            return true;
        }

        public override void ModifyItemLoot(ItemLoot itemLoot)
        {
            itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.AmuletOfDuat>(), 1, 1, 1));
            itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.KhopeshOfAnubis>(), 3, 1, 1));
            itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.JudgementStaff>(), 3, 1, 1));
            itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.DuatShard>(), 1, 12, 20));
            itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.BowOfHorus>(), 3, 1, 1));
            itemLoot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<NPCs.Anubis>()));
        }
    }
}
