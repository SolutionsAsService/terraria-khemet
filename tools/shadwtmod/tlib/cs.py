"""cs: emit the C# (tModLoader 1.4.4) for every content spec: items, tiles, projectiles, enemies, bosses, the world system and the pyramid generator.

Every emitter returns the text of one .cs file. The shapes follow tModLoader's own ExampleMod: SetDefaults sets stats, ModifyNPCLoot adds
ItemDropRules, a boss is a ModNPC with a small state machine in AI(). Nothing here is clever: it is the boilerplate, written the same way every time.
"""
from .pyramid import rle

HEAD = "using Microsoft.Xna.Framework;\nusing Terraria;\nusing Terraria.Audio;\nusing Terraria.GameContent.ItemDropRules;\nusing Terraria.ID;\nusing Terraria.ModLoader;\n"
RARITY = {"White": "ItemRarityID.White", "Blue": "ItemRarityID.Blue", "Green": "ItemRarityID.Green", "Orange": "ItemRarityID.Orange", "LightRed": "ItemRarityID.LightRed",
          "Pink": "ItemRarityID.Pink", "LightPurple": "ItemRarityID.LightPurple", "Lime": "ItemRarityID.Lime", "Yellow": "ItemRarityID.Yellow", "Cyan": "ItemRarityID.Cyan",
          "Red": "ItemRarityID.Red", "Purple": "ItemRarityID.Purple", "Expert": "ItemRarityID.Expert"}


def item_ref(s):
    kind, name = s.split(":", 1)
    return f"ModContent.ItemType<Items.{name}>()" if kind == "mod" else f"ItemID.{name}"


def npc_ref(s):
    kind, name = s.split(":", 1)
    return f"ModContent.NPCType<NPCs.{name}>()" if kind == "mod" else f"NPCID.{name}"


def proj_ref(s):
    return f"ModContent.ProjectileType<Projectiles.{s}>()"


def f(v):
    return f"{float(v)}f"


def lines(*parts):
    return "\n".join(parts)


def recipe_block(spec, cls):
    r = spec.get("recipe")
    if not r:
        return ""
    chain = "".join(f".AddIngredient({item_ref(i)}, {n})" for i, n in r["ingredients"])
    st = r.get("station", "vanilla:Anvils")
    kind, name = st.split(":", 1)
    tile = f"TileID.{name}" if kind == "vanilla" else f"ModContent.TileType<Tiles.{name}Tile>()"
    count = f"CreateRecipe({r['count']})" if r.get("count", 1) > 1 else "CreateRecipe()"
    return f"""
        public override void AddRecipes()
        {{
            {count}{chain}.AddTile({tile}).Register();
        }}
"""


def item_cs(spec):
    cls, kind = spec["id"], spec["kind"]
    body, extra_using = [], ""
    size = spec.get("size", [32, 32])
    rare = RARITY[spec.get("rarity", "White")]
    value = spec.get("value", 0)
    common = f"""            Item.width = {size[0]};
            Item.height = {size[1]};
            Item.rare = {rare};
            Item.value = {int(value)};"""
    if kind == "sword":
        undead = spec.get("bonus_vs", [])
        cond = " || ".join(f"target.type == {npc_ref(n)}" for n in undead) or "false"
        body.append(f"""        public override void SetDefaults()
        {{
{common}
            Item.damage = {spec['damage']};
            Item.DamageType = DamageClass.Melee;
            Item.useTime = {spec.get('use_time', 22)};
            Item.useAnimation = {spec.get('use_time', 22)};
            Item.useStyle = ItemUseStyleID.Swing;
            Item.knockBack = {f(spec.get('knockback', 5))};
            Item.UseSound = SoundID.Item1;
            Item.autoReuse = true;
        }}

        public override void ModifyHitNPC(Player player, NPC target, ref NPC.HitModifiers modifiers)
        {{
            if ({cond})
            {{
                modifiers.FinalDamage *= {f(spec.get('bonus_mult', 1.4))};
            }}
        }}""")
    elif kind == "staff":
        body.append(f"""        public override void SetDefaults()
        {{
{common}
            Item.damage = {spec['damage']};
            Item.DamageType = DamageClass.Magic;
            Item.mana = {spec.get('mana', 8)};
            Item.noMelee = true;
            Item.useTime = {spec.get('use_time', 24)};
            Item.useAnimation = {spec.get('use_time', 24)};
            Item.useStyle = ItemUseStyleID.Shoot;
            Item.knockBack = {f(spec.get('knockback', 3))};
            Item.UseSound = SoundID.Item43;
            Item.autoReuse = true;
            Item.shoot = {proj_ref(spec['shoot'])};
            Item.shootSpeed = {f(spec.get('shoot_speed', 10))};
        }}""")
    elif kind == "accessory":
        fx = spec.get("effects", {})
        lines_ = []
        if "life" in fx:
            lines_.append(f"player.statLifeMax2 += {fx['life']};")
        if "mana" in fx:
            lines_.append(f"player.statManaMax2 += {fx['mana']};")
        if "regen" in fx:
            lines_.append(f"player.lifeRegen += {fx['regen']};")
        if "speed" in fx:
            lines_.append(f"player.moveSpeed += {f(fx['speed'])};")
        if "damage" in fx:
            lines_.append(f"player.GetDamage(DamageClass.Generic) += {f(fx['damage'])};")
        if "crit" in fx:
            lines_.append(f"player.GetCritChance(DamageClass.Generic) += {fx['crit']};")
        if "minions" in fx:
            lines_.append(f"player.maxMinions += {fx['minions']};")
        if fx.get("no_fall"):
            lines_.append("player.noFallDmg = true;")
        if "desert_damage" in fx:
            lines_.append(f"if (player.ZoneDesert) {{ player.GetDamage(DamageClass.Generic) += {f(fx['desert_damage'])}; }}")
        inner = "\n            ".join(lines_) or "// no effect"
        body.append(f"""        public override void SetDefaults()
        {{
{common}
            Item.accessory = true;
            Item.defense = {spec.get('defense', 0)};
        }}

        public override void UpdateAccessory(Player player, bool hideVisual)
        {{
            {inner}
        }}""")
    elif kind == "material":
        body.append(f"""        public override void SetStaticDefaults()
        {{
            Item.ResearchUnlockCount = {spec.get('research', 25)};
        }}

        public override void SetDefaults()
        {{
{common}
            Item.maxStack = Item.CommonMaxStack;
        }}""")
    elif kind == "tile":
        body.append(f"""        public override void SetStaticDefaults()
        {{
            Item.ResearchUnlockCount = 100;
        }}

        public override void SetDefaults()
        {{
            Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.{spec['tile']}Tile>());
            Item.width = 16;
            Item.height = 16;
            Item.value = {int(value)};
        }}""")
    elif kind == "summon":
        boss = spec["boss"]
        body.append(f"""        public override void SetStaticDefaults()
        {{
            Item.ResearchUnlockCount = 1;
            ItemID.Sets.SortingPriorityBossSpawns[Type] = 12;
        }}

        public override void SetDefaults()
        {{
{common}
            Item.maxStack = 20;
            Item.useAnimation = 45;
            Item.useTime = 45;
            Item.useStyle = ItemUseStyleID.HoldUp;
            Item.consumable = true;
        }}

        public override bool CanUseItem(Player player)
        {{
            return {"player.ZoneDesert && " if spec.get('desert') else ""}!NPC.AnyNPCs(ModContent.NPCType<NPCs.{boss}>());
        }}

        public override bool? UseItem(Player player)
        {{
            if (player.whoAmI == Main.myPlayer)
            {{
                SoundEngine.PlaySound(SoundID.Roar, player.position);
                int type = ModContent.NPCType<NPCs.{boss}>();
                if (Main.netMode != NetmodeID.MultiplayerClient)
                {{
                    NPC.SpawnOnPlayer(player.whoAmI, type);
                }}
                else
                {{
                    NetMessage.SendData(MessageID.SpawnBossUseLicenseStartEvent, number: player.whoAmI, number2: type);
                }}
            }}
            return true;
        }}""")
    elif kind == "bag":
        drops = "\n            ".join(f"itemLoot.Add(ItemDropRule.Common({item_ref(d['item'])}, {d.get('denom', 1)}, {d.get('min', 1)}, {d.get('max', 1)}));" for d in spec["drops"])
        body.append(f"""        public override void SetStaticDefaults()
        {{
            ItemID.Sets.BossBag[Type] = true;
            ItemID.Sets.PreHardmodeLikeBossBag[Type] = {"true" if spec.get('prehardmode') else "false"};
            Item.ResearchUnlockCount = 3;
        }}

        public override void SetDefaults()
        {{
            Item.maxStack = Item.CommonMaxStack;
            Item.consumable = true;
            Item.width = 30;
            Item.height = 32;
            Item.rare = ItemRarityID.Expert;
            Item.expert = true;
        }}

        public override bool CanRightClick()
        {{
            return true;
        }}

        public override void ModifyItemLoot(ItemLoot itemLoot)
        {{
            {drops}
            itemLoot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<NPCs.{spec['boss']}>()));
        }}""")
    else:
        raise ValueError(f"item {cls}: unknown kind {kind}")
    return f"""{HEAD}
namespace Khemet.Items
{{
    public class {cls} : ModItem
    {{
{chr(10).join(body)}
{recipe_block(spec, cls)}    }}
}}
"""


def tile_cs(spec):
    cls = spec["id"] + "Tile"
    col = spec.get("map_color", "#c4aa70").lstrip("#")
    r, g, b = int(col[0:2], 16), int(col[2:4], 16), int(col[4:6], 16)
    return f"""{HEAD}
namespace Khemet.Tiles
{{
    public class {cls} : ModTile
    {{
        public override void SetStaticDefaults()
        {{
            Main.tileSolid[Type] = true;
            Main.tileMergeDirt[Type] = true;
            Main.tileBlockLight[Type] = true;
            AddMapEntry(new Color({r}, {g}, {b}));
            DustType = DustID.{spec.get('dust', 'Sand')};
            HitSound = SoundID.Tink;
            MineResist = {f(spec.get('resist', 2))};
            MinPick = {spec.get('min_pick', 0)};
        }}
    }}
}}
"""


def projectile_cs(spec):
    cls = spec["id"]
    size = spec.get("size", [18, 18])
    lr, lg, lb = spec.get("light", [1.0, 0.8, 0.3])
    hostile = spec.get("hostile", True)
    owner = ("Projectile.hostile = true;\n            Projectile.friendly = false;" if hostile else
             "Projectile.friendly = true;\n            Projectile.hostile = false;\n            Projectile.DamageType = DamageClass.Magic;")
    return f"""{HEAD}
namespace Khemet.Projectiles
{{
    public class {cls} : ModProjectile
    {{
        public override void SetDefaults()
        {{
            Projectile.width = {size[0]};
            Projectile.height = {size[1]};
            {owner}
            Projectile.penetrate = {spec.get('penetrate', -1 if hostile else 3)};
            Projectile.timeLeft = {spec.get('time', 240)};
            Projectile.tileCollide = {"true" if spec.get('tile_collide', not hostile) else "false"};
            Projectile.ignoreWater = true;
        }}

        public override void AI()
        {{
            Projectile.rotation = Projectile.velocity.ToRotation() + MathHelper.PiOver2;
            Lighting.AddLight(Projectile.Center, {f(lr)}, {f(lg)}, {f(lb)});
            if (Main.rand.NextBool(3))
            {{
                Dust.NewDust(Projectile.position, Projectile.width, Projectile.height, DustID.{spec.get('dust', 'Torch')}, 0f, 0f, 100, default(Color), 1.2f);
            }}
        }}
    }}
}}
"""


def drops_rules(drops, indent="            "):
    out = []
    for d in drops:
        out.append(f"{indent}npcLoot.Add(ItemDropRule.Common({item_ref(d['item'])}, {d.get('denom', 1)}, {d.get('min', 1)}, {d.get('max', 1)}));")
    return "\n".join(out)


def enemy_cs(spec):
    cls = spec["id"]
    size = spec["size"]
    ai = spec.get("ai", "fighter")
    sp = spec.get("spawn", {})
    ai_lines = ("NPC.aiStyle = NPCAIStyleID.Fighter;\n            AIType = NPCID.Zombie;\n            AnimationType = NPCID.Zombie;" if ai == "fighter" else
                "NPC.aiStyle = NPCAIStyleID.Bat;\n            AIType = NPCID.CaveBat;\n            AnimationType = NPCID.CaveBat;\n            NPC.noGravity = true;")
    frames = 3 if ai == "fighter" else 4
    return f"""{HEAD}
namespace Khemet.NPCs
{{
    public class {cls} : ModNPC
    {{
        public override void SetStaticDefaults()
        {{
            Main.npcFrameCount[Type] = {frames};
        }}

        public override void SetDefaults()
        {{
            NPC.width = {size[0]};
            NPC.height = {size[1]};
            NPC.damage = {spec['damage']};
            NPC.defense = {spec['defense']};
            NPC.lifeMax = {spec['life']};
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.knockBackResist = {f(spec.get('kb', 0.5))};
            NPC.value = {f(spec.get('value', 60))};
            {ai_lines}
        }}

        public override float SpawnChance(NPCSpawnInfo spawnInfo)
        {{
            if (Systems.KhemetWorld.InPyramid(spawnInfo.Player))
            {{
                return {f(sp.get('pyramid', 0.5))};
            }}
            return spawnInfo.Player.ZoneDesert ? {f(sp.get('desert', 0.1))} : 0f;
        }}

        public override void ModifyNPCLoot(NPCLoot npcLoot)
        {{
{drops_rules(spec.get('drops', []))}
        }}
    }}
}}
"""


def boss_cs(spec):
    cls = spec["id"]
    w, h = spec["size"]
    atk = spec["attacks"]
    hover = spec.get("hover", {"height": 260, "speed": 9})
    flag = spec["flag"]
    dash, volley, summon = atk.get("dash"), atk.get("volley"), atk.get("summon")
    choices = [i for i, a in enumerate((dash, volley, summon), start=1) if a]
    n = len(choices)
    case_dash = f"""
                case 1: // a dash: three passes at the player, each telegraphed
                {{
                    if (timer < 30f)
                    {{
                        NPC.velocity *= 0.9f;
                    }}
                    else if (timer == 30f)
                    {{
                        NPC.velocity = (target.Center - NPC.Center).SafeNormalize(Vector2.UnitY) * {f(dash['speed'] if dash else 0)} * (enraged ? 1.25f : 1f);
                        SoundEngine.PlaySound(SoundID.Roar, NPC.Center);
                    }}
                    else if (timer > 56f)
                    {{
                        count++;
                        timer = 0f;
                        if (count >= {dash['passes'] if dash else 1}f)
                        {{
                            ToHover();
                        }}
                    }}
                    break;
                }}""" if dash else ""
    case_volley = f"""
                case 2: // a volley: a fan of bolts from the front, three times
                {{
                    NPC.velocity *= 0.92f;
                    if (timer % {volley['interval'] if volley else 20}f == 0f && Main.netMode != NetmodeID.MultiplayerClient)
                    {{
                        Vector2 aim = (target.Center - NPC.Center).SafeNormalize(Vector2.UnitY);
                        int shots = {volley['count'] if volley else 3} + (enraged ? 2 : 0);
                        for (int i = 0; i < shots; i++)
                        {{
                            float spread = ((i - (shots - 1) / 2f) * {f(volley['spread'] if volley else 0.2)});
                            Vector2 vel = aim.RotatedBy(spread) * {f(volley['speed'] if volley else 8)};
                            Projectile.NewProjectile(NPC.GetSource_FromAI(), NPC.Center, vel, {proj_ref(volley['projectile']) if volley else '0'}, {volley['damage'] if volley else 0}, 0f, Main.myPlayer);
                        }}
                        SoundEngine.PlaySound(SoundID.Item20, NPC.Center);
                    }}
                    if (timer > {(volley['interval'] if volley else 20) * 3 + 10}f)
                    {{
                        ToHover();
                    }}
                    break;
                }}""" if volley else ""
    case_summon = f"""
                case 3: // a summons: minions from the tomb
                {{
                    NPC.velocity *= 0.92f;
                    if (timer == 30f && Main.netMode != NetmodeID.MultiplayerClient)
                    {{
                        int minions = {summon['count'] if summon else 2} + (enraged ? 1 : 0);
                        for (int i = 0; i < minions; i++)
                        {{
                            NPC.NewNPC(NPC.GetSource_FromAI(), (int)NPC.Center.X + (i - minions / 2) * 40, (int)NPC.Center.Y, {npc_ref(summon['npc']) if summon else '0'});
                        }}
                        SoundEngine.PlaySound(SoundID.Item8, NPC.Center);
                    }}
                    if (timer > 70f)
                    {{
                        ToHover();
                    }}
                    break;
                }}""" if summon else ""
    pick = " ".join(f"case {k}: state = {c}f; break;" for k, c in enumerate(choices))
    drops = drops_rules(spec.get("drops", []), "                ")
    return f"""{HEAD}
namespace Khemet.NPCs
{{
    [AutoloadBossHead]
    public class {cls} : ModNPC
    {{
        private int hoverTimer;

        public override void SetStaticDefaults()
        {{
            Main.npcFrameCount[Type] = 4;
            NPCID.Sets.MPAllowedEnemies[Type] = true;
        }}

        public override void SetDefaults()
        {{
            NPC.width = {w};
            NPC.height = {h};
            NPC.damage = {spec['damage']};
            NPC.defense = {spec['defense']};
            NPC.lifeMax = {spec['life']};
            NPC.HitSound = SoundID.NPCHit54;
            NPC.DeathSound = SoundID.NPCDeath6;
            NPC.knockBackResist = 0f;
            NPC.value = Item.buyPrice(gold: {spec.get('gold', 5)});
            NPC.aiStyle = -1;
            NPC.noGravity = true;
            NPC.noTileCollide = true;
            NPC.boss = true;
            NPC.npcSlots = 10f;
            NPC.lavaImmune = true;
            Music = MusicID.{spec.get('music', 'Boss2')};
        }}

        public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment)
        {{
            NPC.lifeMax = (int)(NPC.lifeMax * 0.75f * bossAdjustment);
            NPC.damage = (int)(NPC.damage * 0.75f);
        }}

        private void ToHover()
        {{
            NPC.ai[0] = 0f;
            NPC.ai[1] = 0f;
            NPC.ai[2] = 0f;
            hoverTimer = 0;
        }}

        public override void AI()
        {{
            NPC.TargetClosest(true);
            Player target = Main.player[NPC.target];
            if (!target.active || target.dead)
            {{
                NPC.velocity.Y -= 0.4f;
                NPC.EncourageDespawn(60);
                return;
            }}
            bool enraged = NPC.life < NPC.lifeMax * 0.5f;
            ref float state = ref NPC.ai[0];
            ref float timer = ref NPC.ai[1];
            ref float count = ref NPC.ai[2];
            timer++;
            NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
            NPC.rotation = NPC.velocity.X * 0.02f;
            switch ((int)state)
            {{
                default:
                case 0: // hover above the player, then choose an attack
                {{
                    hoverTimer++;
                    float side = (float)System.Math.Sin(hoverTimer * 0.02f) * 320f;
                    Vector2 home = target.Center + new Vector2(side, -{hover['height']}f);
                    Vector2 desired = (home - NPC.Center).SafeNormalize(Vector2.Zero) * {f(hover['speed'])} * (enraged ? 1.3f : 1f);
                    NPC.velocity = Vector2.Lerp(NPC.velocity, desired, 0.06f);
                    if (timer > (enraged ? 70f : 110f))
                    {{
                        timer = 0f;
                        count = 0f;
                        switch (Main.rand.Next({n}))
                        {{
                            {pick}
                        }}
                    }}
                    break;
                }}{case_dash}{case_volley}{case_summon}
            }}
        }}

        public override void FindFrame(int frameHeight)
        {{
            NPC.frameCounter++;
            if (NPC.frameCounter > 7)
            {{
                NPC.frameCounter = 0;
                NPC.frame.Y = (NPC.frame.Y + frameHeight) % (frameHeight * Main.npcFrameCount[Type]);
            }}
        }}

        public override void ModifyNPCLoot(NPCLoot npcLoot)
        {{
            npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<Items.{spec['bag']}>()));
            LeadingConditionRule notExpert = new LeadingConditionRule(new Conditions.NotExpert());
            {chr(10).join("            notExpert.OnSuccess(ItemDropRule.Common(" + item_ref(d['item']) + ", " + str(d.get('denom', 1)) + ", " + str(d.get('min', 1)) + ", " + str(d.get('max', 1)) + "));" for d in spec.get('drops', []))}
            npcLoot.Add(notExpert);
        }}

        public override void OnKill()
        {{
            Systems.KhemetWorld.{flag} = true;
            if (Main.netMode == NetmodeID.Server)
            {{
                NetMessage.SendData(MessageID.WorldData);
            }}
        }}
    }}
}}
"""


def world_cs(flags):
    decl = "\n".join(f"        public static bool {f_};" for f_ in flags)
    clear = "\n".join(f"            {f_} = false;" for f_ in flags)
    save = "\n".join(f'            if ({f_}) {{ tag["{f_}"] = true; }}' for f_ in flags)
    load = "\n".join(f'            {f_} = tag.ContainsKey("{f_}");' for f_ in flags)
    send = "\n".join(f"            writer.Write({f_});" for f_ in flags)
    recv = "\n".join(f"            {f_} = reader.ReadBoolean();" for f_ in flags)
    return f"""using System.IO;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Khemet.Systems
{{
    /// <summary>World state: which bosses have fallen, and where the Grand Pyramid stands (tile coordinates).</summary>
    public class KhemetWorld : ModSystem
    {{
{decl}
        public static Rectangle PyramidArea;

        public static bool InPyramid(Player player)
        {{
            return PyramidArea.Width > 0 && PyramidArea.Contains(player.Center.ToTileCoordinates());
        }}

        public override void ClearWorld()
        {{
{clear}
            PyramidArea = Rectangle.Empty;
        }}

        public override void SaveWorldData(TagCompound tag)
        {{
{save}
            tag["pyX"] = PyramidArea.X;
            tag["pyY"] = PyramidArea.Y;
            tag["pyW"] = PyramidArea.Width;
            tag["pyH"] = PyramidArea.Height;
        }}

        public override void LoadWorldData(TagCompound tag)
        {{
{load}
            PyramidArea = new Rectangle(tag.GetInt("pyX"), tag.GetInt("pyY"), tag.GetInt("pyW"), tag.GetInt("pyH"));
        }}

        public override void NetSend(BinaryWriter writer)
        {{
{send}
            writer.Write(PyramidArea.X);
            writer.Write(PyramidArea.Y);
            writer.Write(PyramidArea.Width);
            writer.Write(PyramidArea.Height);
        }}

        public override void NetReceive(BinaryReader reader)
        {{
{recv}
            PyramidArea = new Rectangle(reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32(), reader.ReadInt32());
        }}
    }}
}}
"""


def blueprint_cs(bp):
    rows = ",\n            ".join('"' + rle(r) + '"' for r in bp["rows"])
    return f"""namespace Khemet.Systems
{{
    /// <summary>The Grand Pyramid, drawn one character per tile and run-length encoded (generated from content/structures.json by shadw-mod; do not edit).
    /// {bp['width']} wide, {bp['height']} tall, the ground at row {bp['ground_row']}.</summary>
    public static class PyramidBlueprint
    {{
        public const int Width = {bp['width']};
        public const int Height = {bp['height']};
        public const int GroundRow = {bp['ground_row']};

        public static readonly string[] Rows = new string[]
        {{
            {rows}
        }};

        /// <summary>Row {{r}} as one character per tile.</summary>
        public static string Decode(int r)
        {{
            string s = Rows[r];
            var sb = new System.Text.StringBuilder();
            int i = 0;
            while (i < s.Length)
            {{
                char c = s[i++];
                int n = 0;
                while (i < s.Length && char.IsDigit(s[i]))
                {{
                    n = n * 10 + (s[i++] - '0');
                }}
                sb.Append(c, n);
            }}
            return sb.ToString();
        }}
    }}
}}
"""


def pyramid_gen_cs(spec, bp):
    loot = spec.get("chest_loot", {})
    cases = []
    for role, items in loot.items():
        body = "\n".join(
            f"                    if (WorldGen.genRand.Next({max(1, round(1 / it.get('chance', 1)))}) == 0) {{ Put(chest, ref slot, {item_ref(it['item'])}, WorldGen.genRand.Next({it.get('min', 1)}, {it.get('max', 1) + 1})); }}" for it in items)
        cases.append(f'                case "{role}":\n{body}\n                    break;')
    cases = "\n".join(cases)
    roles = "\n".join(f'            new int[] {{ {x}, {y} }},' for (x, y, _) in bp["chests"])
    role_names = ", ".join(f'"{r}"' for (_, _, r) in bp["chests"])
    return f"""using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.Generation;
using Terraria.ID;
using Terraria.IO;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Khemet.Systems
{{
    /// <summary>Adds the Grand Pyramid to world generation, after the vanilla Pyramids pass: finds the sandiest flat stretch of desert, levels it and
    /// places the blueprint tile by tile, then stocks the chests by role.</summary>
    public class PyramidGenSystem : ModSystem
    {{
        private static readonly int[][] ChestCells = new int[][]
        {{
{roles}
        }};

        private static readonly string[] ChestRoles = new string[] {{ {role_names} }};

        public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight)
        {{
            int index = tasks.FindIndex(pass => pass.Name.Equals("Pyramids"));
            if (index == -1)
            {{
                index = tasks.Count - 1;
            }}
            tasks.Insert(index + 1, new PassLegacy("Grand Pyramid of Khemet", GenerateGrandPyramid));
        }}

        private static int SurfaceY(int x)
        {{
            for (int y = 60; y < (int)Main.worldSurface; y++)
            {{
                Tile tile = Main.tile[x, y];
                if (tile.HasTile && Main.tileSolid[tile.TileType])
                {{
                    return y;
                }}
            }}
            return -1;
        }}

        private static bool IsSand(int type)
        {{
            return type == TileID.Sand || type == TileID.HardenedSand || type == TileID.Sandstone;
        }}

        private static void Put(Chest chest, ref int slot, int type, int stack)
        {{
            if (slot < 40)
            {{
                chest.item[slot].SetDefaults(type);
                chest.item[slot].stack = stack;
                slot++;
            }}
        }}

        private static void GenerateGrandPyramid(GenerationProgress progress, GameConfiguration configuration)
        {{
            progress.Message = "Raising the Grand Pyramid of Khemet";
            int W = PyramidBlueprint.Width;
            int H = PyramidBlueprint.Height;
            int groundRow = PyramidBlueprint.GroundRow;
            int bestX = -1;
            double bestScore = -1.0;
            for (int attempt = 0; attempt < 400; attempt++)
            {{
                int x0 = WorldGen.genRand.Next(Main.maxTilesX / 8, Main.maxTilesX * 7 / 8 - W);
                int sand = 0;
                int count = 0;
                int minY = int.MaxValue;
                int maxY = 0;
                for (int x = x0; x < x0 + W; x += 3)
                {{
                    int y = SurfaceY(x);
                    if (y < 0)
                    {{
                        continue;
                    }}
                    count++;
                    minY = Math.Min(minY, y);
                    maxY = Math.Max(maxY, y);
                    if (IsSand(Main.tile[x, y].TileType))
                    {{
                        sand++;
                    }}
                }}
                if (count == 0)
                {{
                    continue;
                }}
                double score = sand / (double)count * 100.0 - (maxY - minY) * 1.5;
                if (score > bestScore)
                {{
                    bestScore = score;
                    bestX = x0;
                }}
            }}
            if (bestX < 0)
            {{
                return;
            }}
            // the ground line is the median surface across the site
            List<int> ys = new List<int>();
            for (int x = bestX; x < bestX + W; x += 2)
            {{
                int y = SurfaceY(x);
                if (y > 0)
                {{
                    ys.Add(y);
                }}
            }}
            ys.Sort();
            int ground = ys[ys.Count / 2];
            int top = ground - groundRow;
            // clear the sky above the site and fill any hollow below the ground line with sandstone, so the foundation sits on solid ground
            for (int x = bestX; x < bestX + W; x++)
            {{
                for (int y = top - 2; y < ground; y++)
                {{
                    Main.tile[x, y].ClearEverything();
                }}
                for (int y = ground; y < ground + 3; y++)
                {{
                    WorldGen.PlaceTile(x, y, TileID.Sandstone, true, true);
                }}
            }}
            // place the blueprint
            Dictionary<char, int> tiles = new Dictionary<char, int>();
            tiles['B'] = ModContent.TileType<Tiles.PharaohBrickTile>();
            tiles['G'] = ModContent.TileType<Tiles.GoldenSandstoneTile>();
            tiles['H'] = ModContent.TileType<Tiles.HieroglyphBrickTile>();
            tiles['L'] = ModContent.TileType<Tiles.LapisInlayTile>();
            for (int r = 0; r < H; r++)
            {{
                progress.Set(r / (float)H);
                string row = PyramidBlueprint.Decode(r);
                for (int c = 0; c < W; c++)
                {{
                    char ch = row[c];
                    int x = bestX + c;
                    int y = top + r;
                    if (ch == ' ')
                    {{
                        continue;
                    }}
                    Tile tile = Main.tile[x, y];
                    if (ch == '.' || ch == 'c' || ch == 'C' || ch == 'T' || ch == 'p' || ch == 'K')
                    {{
                        tile.ClearEverything();
                        tile.WallType = WallID.SandstoneBrick;
                    }}
                    else
                    {{
                        tile.ClearEverything();
                        WorldGen.PlaceTile(x, y, tiles[ch], true, true);
                    }}
                }}
            }}
            // the pieces that need a neighbour: platforms, spikes and torches (after the walls and floors exist), then the chests
            for (int r = 0; r < H; r++)
            {{
                string row = PyramidBlueprint.Decode(r);
                for (int c = 0; c < W; c++)
                {{
                    int x = bestX + c;
                    int y = top + r;
                    switch (row[c])
                    {{
                        case 'p':
                            WorldGen.PlaceTile(x, y, TileID.Platforms, true, true, -1, 0);
                            break;
                        case 'K':
                            WorldGen.PlaceTile(x, y, TileID.Spikes, true, true);
                            break;
                        case 'T':
                            WorldGen.PlaceTile(x, y, TileID.Torches, true, false, -1, 0);
                            break;
                    }}
                }}
            }}
            for (int i = 0; i < ChestCells.Length; i++)
            {{
                int cx = bestX + ChestCells[i][0];
                int cy = top + ChestCells[i][1];
                int index = WorldGen.PlaceChest(cx, cy, (ushort)TileID.Containers, false, 1);
                if (index < 0)
                {{
                    continue;
                }}
                Chest chest = Main.chest[index];
                int slot = 0;
                switch (ChestRoles[i])
                {{
{cases}
                }}
            }}
            Systems.KhemetWorld.PyramidArea = new Rectangle(bestX, top, W, H);
        }}
    }}
}}
"""


def mod_cs():
    return """using Terraria.ModLoader;

namespace Khemet
{
    /// <summary>The Khemet mod. Everything it adds is a class under Items, Tiles, NPCs, Projectiles and Systems, generated from content/*.json.</summary>
    public class KhemetMod : Mod
    {
    }
}
"""


def hjson(spec_items, tiles, npcs, projs):
    def block(title, entries):
        out = [f"\t\t{title}: {{"]
        for cls, vals in entries:
            out.append(f"\t\t\t{cls}: {{")
            for k, v in vals.items():
                out.append(f"\t\t\t\t{k}: '''{v}'''")
            out.append("\t\t\t}")
        out.append("\t\t}")
        return "\n".join(out)
    items = [(i["id"], {"DisplayName": i["name"], "Tooltip": i.get("tooltip", "")}) for i in spec_items]
    items += [(t["id"], {"DisplayName": t["name"], "Tooltip": ""}) for t in tiles if t.get("item", True)]
    parts = [block("Items", items)]
    if npcs:
        parts.append(block("NPCs", [(n["id"], {"DisplayName": n["name"]}) for n in npcs]))
    if projs:
        parts.append(block("Projectiles", [(p["id"], {"DisplayName": p["name"]}) for p in projs]))
    return "Mods: {\n\tKhemet: {\n" + "\n".join(parts) + "\n\t}\n}\n"
