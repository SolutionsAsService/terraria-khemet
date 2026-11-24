using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Khemet.NPCs
{
    public class ScarabSwarm : ModNPC
    {
        public override void SetStaticDefaults()
        {
            Main.npcFrameCount[Type] = 4;
        }

        public override void SetDefaults()
        {
            NPC.width = 30;
            NPC.height = 24;
            NPC.damage = 18;
            NPC.defense = 2;
            NPC.lifeMax = 24;
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.knockBackResist = 0.8f;
            NPC.value = 40.0f;
            NPC.aiStyle = NPCAIStyleID.Bat;
            AIType = NPCID.CaveBat;
            AnimationType = NPCID.CaveBat;
            NPC.noGravity = true;
        }

        public override float SpawnChance(NPCSpawnInfo spawnInfo)
        {
            if (Systems.KhemetWorld.InArea(spawnInfo.Player, Systems.KhemetWorld.GrandPyramidArea))
            {
                return 0.9f;
            }
            return spawnInfo.Player.ZoneDesert ? 0.12f : 0f;
        }

        public override void ModifyNPCLoot(NPCLoot npcLoot)
        {

        }
    }
}
