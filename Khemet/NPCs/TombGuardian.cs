using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.NPCs
{
    public class TombGuardian : ModNPC
    {
        public override void SetStaticDefaults()
        {
            Main.npcFrameCount[Type] = 3;
        }

        public override void SetDefaults()
        {
            NPC.width = 40;
            NPC.height = 56;
            NPC.damage = 38;
            NPC.defense = 14;
            NPC.lifeMax = 240;
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.knockBackResist = 0.2f;
            NPC.value = 600.0f;
            NPC.aiStyle = NPCAIStyleID.Fighter;
            AIType = NPCID.Zombie;
            AnimationType = NPCID.Zombie;
        }

        public override float SpawnChance(NPCSpawnInfo spawnInfo)
        {
            if (Systems.KhemetWorld.InPyramid(spawnInfo.Player))
            {
                return 0.5f;
            }
            return spawnInfo.Player.ZoneDesert ? 0.02f : 0f;
        }

        public override void ModifyNPCLoot(NPCLoot npcLoot)
        {
            npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.SunstoneShard>(), 2, 1, 3));
            npcLoot.Add(ItemDropRule.Common(ItemID.GoldCoin, 3, 1, 2));
        }
    }
}
