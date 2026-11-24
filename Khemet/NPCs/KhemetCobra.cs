using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.NPCs
{
    public class KhemetCobra : ModNPC
    {
        public override void SetStaticDefaults()
        {
            Main.npcFrameCount[Type] = 3;
        }

        public override void SetDefaults()
        {
            NPC.width = 34;
            NPC.height = 48;
            NPC.damage = 22;
            NPC.defense = 6;
            NPC.lifeMax = 70;
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.knockBackResist = 0.5f;
            NPC.value = 120.0f;
            NPC.aiStyle = NPCAIStyleID.Fighter;
            AIType = NPCID.Zombie;
            AnimationType = NPCID.Zombie;
        }

        public override float SpawnChance(NPCSpawnInfo spawnInfo)
        {
            if (Systems.KhemetWorld.InArea(spawnInfo.Player, Systems.KhemetWorld.GrandPyramidArea))
            {
                return 0.6f;
            }
            return spawnInfo.Player.ZoneDesert ? 0.1f : 0f;
        }

        public override void ModifyNPCLoot(NPCLoot npcLoot)
        {
            npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Items.SunstoneShard>(), 4, 1, 2));
        }
    }
}
