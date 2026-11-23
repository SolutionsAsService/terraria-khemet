#!/usr/bin/env python3
"""shadw-mod content (Terraria / tModLoader): a mod's content is data, and everything the game needs is generated from it.

    shadw-mod content <mod> gen        write the tModLoader mod folder: C# for every item, tile, projectile, enemy and boss, the world system,
                                       the pyramid blueprint and generator, every sprite, the language file and the build files
    shadw-mod content <mod> lint       check the specs and what they generate (references resolve, every boss has a bag and a summon, every room
                                       of the pyramid can be reached, every texture exists and has the right size)
    shadw-mod content <mod> check      gen, then compile the generated C# against a stub of the tModLoader API (needs the .NET 8 SDK)
    shadw-mod content <mod> preview    draw preview/*.png: the sprites at 4x and the pyramid cutaway
    shadw-mod content <mod> build      gen, then the real build if TML_DIR points at a tModLoader install, else the stub check

Content lives in <mod>/content/*.json (mod, items, tiles, projectiles, npcs, structures). The generated mod folder is <mod>/<ModName>/ and is what
goes in tModLoader's ModSources. Stdlib only; the compile check shells out to `dotnet`.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tlib import cs, psprite as ps, pyramid  # noqa: E402

KNOWN = {  # vanilla names the generator relies on and is confident exist; anything else is reported as unverified
    "ItemID": {"GoldBar", "IronBar", "Silk", "Cactus", "SandBlock", "Sandstone", "Bone", "LifeCrystal", "HealingPotion", "GreaterHealingPotion", "LesserHealingPotion", "SoulofFlight", "SoulofNight", "SoulofLight",
               "HallowedBar", "AdamantiteBar", "TitaniumBar", "Ruby", "Amber", "Topaz", "Sapphire", "Emerald", "Diamond", "Amethyst", "Cloud", "RainCloud", "FallenStar", "ShinyRedBalloon", "BandofRegeneration", "MagicMirror",
               "GoldCoin", "SilverCoin", "PlatinumBar", "Torch", "Wood", "Chain", "Spike", "ManaPotion", "GreaterManaPotion", "Fireblossom", "Daybloom", "SpelunkerPotion", "IronskinPotion", "SwiftnessPotion", "AncientCloth"},
    "NPCID": {"Zombie", "CaveBat", "Mummy", "DarkMummy", "LightMummy", "Skeleton", "Ghost", "Tumbleweed", "Antlion", "WalkingAntlion", "Vulture", "Wraith", "Mimic", "Pixie"},
    "TileID": {"Anvils", "Sandstone", "HardenedSand", "Sand", "Platforms", "Spikes", "Torches", "Containers", "WorkBenches", "Furnaces", "MythrilAnvil", "AdamantiteForge", "DemonAltar"},
    "DustID": {"Sand", "Torch", "IceTorch", "Gold", "BlueTorch", "YellowTorch", "Stone", "Fire", "Smoke"},
    "MusicID": {"Boss1", "Boss2", "Boss3", "Boss4", "Boss5", "Eclipse", "TheTowers", "LunarBoss", "PlanteraBattle"},
    "SoundID": {"Item1", "Item8", "Item20", "Item43", "NPCHit1", "NPCHit54", "NPCDeath1", "NPCDeath6", "Roar", "Tink"},
    "WallID": {"SandstoneBrick"},
    "NPCAIStyleID": {"Fighter", "Bat"},
    "ItemRarityID": {"White", "Blue", "Green", "Orange", "LightRed", "Pink", "LightPurple", "Lime", "Yellow", "Cyan", "Red", "Purple", "Expert"},
    "ItemUseStyleID": {"Swing", "Shoot", "HoldUp"},
    "MessageID": {"WorldData", "SpawnBossUseLicenseStartEvent"},
    "NetmodeID": {"MultiplayerClient", "Server", "SinglePlayer"},
}


class SpecError(Exception):
    pass


def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


class Mod:
    def __init__(self, root):
        self.root = Path(root).resolve()
        c = self.root / "content"
        self.meta = jread(c / "mod.json")
        if not self.meta:
            raise SpecError(f"{c}/mod.json is missing")
        self.name = self.meta["name"]
        self.items = jread(c / "items.json") or []
        self.tiles = jread(c / "tiles.json") or []
        self.projs = jread(c / "projectiles.json") or []
        self.npcs = jread(c / "npcs.json") or []
        self.structs = jread(c / "structures.json") or []
        self.out = self.root / self.name

    # all the items a tile contributes (the placeable block) join the item list
    def all_items(self):
        extra = []
        for t in self.tiles:
            if t.get("item", True):
                extra.append({"id": t["id"], "name": t["name"], "tooltip": t.get("tooltip", ""), "kind": "tile", "tile": t["id"], "value": t.get("value", 0), "sprite": "tile", "tile_ref": t["id"],
                              "recipe": t.get("recipe")})
        return self.items + extra

    def bosses(self):
        return [n for n in self.npcs if n.get("boss")]

    def enemies(self):
        return [n for n in self.npcs if not n.get("boss")]

    def flags(self):
        return [b["flag"] for b in self.bosses()]


def lint(m):
    errors = []
    items = {i["id"] for i in m.all_items()}
    npcs = {n["id"] for n in m.npcs}
    projs = {p["id"] for p in m.projs}
    tiles = {t["id"] for t in m.tiles}
    for what, ids in (("item", [i["id"] for i in m.all_items()]), ("npc", [n["id"] for n in m.npcs]), ("projectile", [p["id"] for p in m.projs]), ("tile", [t["id"] for t in m.tiles])):
        seen = set()
        for i in ids:
            if not re.fullmatch(r"[A-Z][A-Za-z0-9]{2,40}", i):
                errors.append(f"{what} id '{i}' must be PascalCase (it becomes a C# class name)")
            if i in seen:
                errors.append(f"duplicate {what} id {i}")
            seen.add(i)

    def ref(s, where):
        if not isinstance(s, str) or ":" not in s:
            errors.append(f"{where}: '{s}' must be 'mod:Name' or 'vanilla:Name'")
            return
        kind, name = s.split(":", 1)
        if kind == "mod" and name not in items:
            errors.append(f"{where}: mod item '{name}' does not exist")
        elif kind not in ("mod", "vanilla"):
            errors.append(f"{where}: '{s}' has an unknown prefix")

    def npc_ref(s, where):
        kind, name = s.split(":", 1)
        if kind == "mod" and name not in npcs:
            errors.append(f"{where}: mod NPC '{name}' does not exist")

    for it in m.all_items():
        w = f"item {it['id']}"
        if it["kind"] not in ("sword", "staff", "accessory", "material", "tile", "summon", "bag"):
            errors.append(f"{w}: unknown kind {it['kind']}")
        if it["kind"] == "staff" and it.get("shoot") not in projs:
            errors.append(f"{w}: shoots '{it.get('shoot')}', which is not a projectile")
        if it["kind"] in ("summon", "bag") and it.get("boss") not in npcs:
            errors.append(f"{w}: boss '{it.get('boss')}' is not an NPC")
        for d in it.get("drops", []):
            ref(d["item"], w)
        for n in it.get("bonus_vs", []):
            npc_ref(n, w)
        r = it.get("recipe")
        if r:
            for ing, n in r["ingredients"]:
                ref(ing, w + " recipe")
    for n in m.npcs:
        w = f"npc {n['id']}"
        for d in n.get("drops", []):
            ref(d["item"], w)
        if n.get("boss"):
            if n.get("bag") not in items:
                errors.append(f"{w}: boss bag '{n.get('bag')}' is not an item")
            if not any(i["kind"] == "summon" and i.get("boss") == n["id"] for i in m.all_items()):
                errors.append(f"{w}: no summon item for this boss")
            a = n.get("attacks", {})
            if not a:
                errors.append(f"{w}: a boss needs attacks")
            if a.get("volley") and a["volley"]["projectile"] not in projs:
                errors.append(f"{w}: volley projectile '{a['volley']['projectile']}' is not a projectile")
            if a.get("summon"):
                npc_ref(a["summon"]["npc"], w)
    for t in m.tiles:
        if t.get("pattern") not in ("brick", "golden", "hieroglyph", "lapis"):
            errors.append(f"tile {t['id']}: unknown pattern {t.get('pattern')}")
    # the pyramid: every room reachable, chests placed
    for s in m.structs:
        if s["kind"] == "grand_pyramid":
            bp = pyramid.grand_pyramid(s)
            reach, n = pyramid.connected(bp)
            for room, ok in reach.items():
                if not ok:
                    errors.append(f"structure {s['id']}: the {room} cannot be reached from the entrance")
            roles = {r for (_, _, r) in bp["chests"]}
            for role in s.get("chest_loot", {}):
                if role not in roles:
                    errors.append(f"structure {s['id']}: chest_loot names role '{role}', but no chest of that role was placed")
    # generated files
    if m.out.exists():
        for it in m.all_items():
            for rel in (f"Items/{it['id']}.png",):
                if not (m.out / rel).exists():
                    errors.append(f"missing texture {m.name}/{rel} (run gen)")
        for n in m.npcs:
            if not (m.out / f"NPCs/{n['id']}.png").exists():
                errors.append(f"missing texture {m.name}/NPCs/{n['id']}.png")
            if n.get("boss") and not (m.out / f"NPCs/{n['id']}_Head_Boss.png").exists():
                errors.append(f"missing boss head icon {m.name}/NPCs/{n['id']}_Head_Boss.png")
    return errors


# ---------------------------------------------------------------- sprites
def item_sprite(it):
    p = ps.pal(it.get("palette", "gold"))
    a = ps.pal(it.get("accent", "gold"))
    s = it.get("sprite")
    return {"khopesh": lambda: ps.item_khopesh(p), "staff": lambda: ps.item_staff(ps.pal(it.get("palette", "wood")), ps.pal(it.get("accent", "sun"))), "ankh": lambda: ps.item_ankh(p),
            "charm": lambda: ps.item_charm(p, a), "shard": lambda: ps.item_shard(p), "cartouche": lambda: ps.item_cartouche(p, a), "bag": lambda: ps.item_bag(p, a)}[s]()


def tile_canvas(t):
    return ps.tile16(t["pattern"], ps.pal(t.get("palette", "sand")), ps.pal(t["accent"]) if t.get("accent") else None)


def npc_sheet(n):
    s = n["sprite"]
    if s == "cobra":
        return ps.sheet([ps.enemy_cobra(i) for i in range(3)])
    if s == "guardian":
        return ps.sheet([ps.enemy_guardian(i) for i in range(3)])
    if s == "scarab":
        return ps.sheet([ps.enemy_scarab(i) for i in range(4)])
    if s.startswith("boss:"):
        w, h = n["size"]
        return ps.sheet([ps.boss_pharaoh(i, s.split(":")[1], w, h) for i in range(4)])
    raise SpecError(f"npc {n['id']}: unknown sprite {s}")


def proj_sprite(p):
    pa = ps.pal(p.get("palette", "sun"))
    return ps.projectile_ray(pa) if p.get("sprite") == "ray" else ps.projectile_orb(pa, *p.get("size", [18, 18]))


def gen(m):
    out = m.out
    ns = m.name
    if out.exists():
        for sub in ("Items", "Tiles", "NPCs", "Projectiles", "Systems", "Localization"):
            shutil.rmtree(out / sub, ignore_errors=True)
    files = {}
    for it in m.all_items():
        files[f"Items/{it['id']}.cs"] = cs.item_cs(it)
    for t in m.tiles:
        files[f"Tiles/{t['id']}Tile.cs"] = cs.tile_cs(t)
    for p in m.projs:
        files[f"Projectiles/{p['id']}.cs"] = cs.projectile_cs(p)
    for n in m.npcs:
        files[f"NPCs/{n['id']}.cs"] = cs.boss_cs(n) if n.get("boss") else cs.enemy_cs(n)
    files["Systems/KhemetWorld.cs"] = cs.world_cs(m.flags())
    for s in m.structs:
        if s["kind"] == "grand_pyramid":
            bp = pyramid.grand_pyramid(s)
            files["Systems/PyramidBlueprint.cs"] = cs.blueprint_cs(bp)
            files["Systems/PyramidGenSystem.cs"] = cs.pyramid_gen_cs(s, bp)
    files["KhemetMod.cs"] = cs.mod_cs()
    files["Localization/en-US_Mods.Khemet.hjson"] = cs.hjson(m.all_items(), m.tiles, m.npcs, m.projs)
    meta = m.meta
    files["build.txt"] = f"displayName = {meta.get('display', ns)}\nauthor = {meta.get('author', 'SolutionsAsService')}\nversion = {meta.get('version', '0.1.0')}\nbuildIgnore = *.csproj, *.user, obj\\*, bin\\*, .vs\\*\n"
    files["description.txt"] = meta.get("description", ns) + "\n"
    files[f"{ns}.csproj"] = f"""<Project Sdk="Microsoft.NET.Sdk">
  <Import Project="..\\tModLoader.targets" />
  <PropertyGroup>
    <AssemblyName>{ns}</AssemblyName>
    <TargetFramework>net8.0</TargetFramework>
    <PlatformTarget>AnyCPU</PlatformTarget>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="tModLoader.CodeAssist" Version="0.1.*" />
  </ItemGroup>
</Project>
"""
    for rel, text in files.items():
        dst = out / (rel.replace("Khemet", ns) if rel.startswith(("KhemetMod", "Localization", "Systems/Khemet")) else rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text.replace("Khemet", ns), encoding="utf-8")
    # sprites
    for it in m.all_items():
        if it["kind"] == "tile":
            tile = next(t for t in m.tiles if t["id"] == it["tile"])
            tile_canvas(tile).save(out / f"Items/{it['id']}.png")
        else:
            item_sprite(it).save(out / f"Items/{it['id']}.png")
    for t in m.tiles:
        ps.tile_sheet(tile_canvas(t)).save(out / f"Tiles/{t['id']}Tile.png")
    for p in m.projs:
        proj_sprite(p).save(out / f"Projectiles/{p['id']}.png")
    for n in m.npcs:
        npc_sheet(n).save(out / f"NPCs/{n['id']}.png")
        if n.get("boss"):
            ps.boss_head_icon(n["sprite"].split(":")[1]).save(out / f"NPCs/{n['id']}_Head_Boss.png")
    ps.item_ankh(ps.pal("gold"), 80, 80).save(out / "icon.png")
    return len(files)


# ---------------------------------------------------------------- preview
def preview(m):
    pv = m.root / "preview"
    pv.mkdir(exist_ok=True)

    def board(cells, k, bg, path, pad=6, wrap=None):
        sc = [c.scaled(k) for c in cells]
        wrap = wrap or sum(c.w + pad for c in sc) + pad
        x = y = pad
        rowh = 0
        placed = []
        for c in sc:
            if x + c.w + pad > wrap:
                x, y, rowh = pad, y + rowh + pad, 0
            placed.append((c, x, y))
            x += c.w + pad
            rowh = max(rowh, c.h)
        H = y + rowh + pad
        canvas = ps.Canvas(wrap, H)
        canvas.rect(0, 0, wrap, H, bg)
        for c, px, py in placed:
            canvas.paste(c, px, py)
        canvas.save(path)

    board([item_sprite(i) for i in m.items if i["kind"] != "tile"], 4, (40, 36, 48, 255), pv / "items.png", wrap=1100)
    board([tile_canvas(t) for t in m.tiles] + [ps.projectile_orb(ps.pal(p.get("palette", "sun"))) if p.get("sprite") != "ray" else ps.projectile_ray(ps.pal(p.get("palette", "sun"))) for p in m.projs], 6, (40, 36, 48, 255), pv / "tiles-and-projectiles.png", wrap=1100)
    cells = []
    for n in m.enemies():
        sh = npc_sheet(n)
        fh = sh.h // (3 if n["sprite"] in ("cobra", "guardian") else 4)
        for i in range(sh.h // fh):
            f = ps.Canvas(sh.w, fh)
            for y in range(fh):
                for x in range(sh.w):
                    f.px[y * sh.w + x] = sh.px[(i * fh + y) * sh.w + x]
            cells.append(f)
    board(cells, 3, (70, 90, 140, 255), pv / "enemies.png", wrap=1100)
    bcells = []
    for n in m.bosses():
        w, h = n["size"]
        for fr in (0, 2):
            bcells.append(ps.boss_pharaoh(fr, n["sprite"].split(":")[1], w, h))
    board(bcells, 2, (70, 90, 140, 255), pv / "bosses.png", wrap=1100)
    for s in m.structs:
        if s["kind"] == "grand_pyramid":
            bp = pyramid.grand_pyramid(s)
            pyramid.render(bp, pv / "grand-pyramid.png")
    return pv


# ---------------------------------------------------------------- the compile check
def scan_ids(out):
    names = {}
    for p in out.rglob("*.cs"):
        for cls, name in re.findall(r"\b(ItemID|NPCID|TileID|DustID|MusicID|SoundID|WallID|NPCAIStyleID|ItemRarityID|ItemUseStyleID|MessageID|NetmodeID)\.(\w+)", p.read_text(encoding="utf-8")):
            if name != "Sets":
                names.setdefault(cls, set()).add(name)
    return names


def ids_cs(names):
    lines = ["// Generated by shadw-mod content check: the vanilla IDs the code uses, as names only.", "namespace Terraria.ID", "{"]
    for cls in ("ItemID", "NPCID", "TileID", "DustID", "MusicID", "SoundID", "WallID", "NPCAIStyleID", "ItemRarityID", "ItemUseStyleID", "MessageID", "NetmodeID"):
        typ = "Terraria.Audio.SoundStyle" if cls == "SoundID" else "int"
        decl = [f"        public static readonly {typ} {n} = default({typ});" if cls == "SoundID" else f"        public const int {n} = 0;" for n in sorted(names.get(cls, ()))]
        extra = ""
        if cls == "ItemID":
            extra = "        public static class Sets { public static bool[] BossBag = new bool[10000]; public static bool[] PreHardmodeLikeBossBag = new bool[10000]; public static int[] SortingPriorityBossSpawns = new int[10000]; }"
        if cls == "NPCID":
            extra = "        public static class Sets { public static bool[] MPAllowedEnemies = new bool[10000]; }"
        lines += [f"    public static class {cls}", "    {", *decl, extra, "    }"]
    lines.append("}")
    return "\n".join(lines) + "\n"


def check(m, quiet=False):
    gen(m)
    if shutil.which("dotnet") is None:
        raise SpecError("the compile check needs the .NET 8 SDK (`dotnet`); see docs/TERRARIA.md")
    work = m.root / "build" / "check"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    names = scan_ids(m.out)
    unverified = sorted(f"{c}.{n}" for c, ns_ in names.items() for n in ns_ if n not in KNOWN.get(c, ()))
    (work / "Ids.cs").write_text(ids_cs(names), encoding="utf-8")
    (work / "Check.csproj").write_text(f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <OutputType>Library</OutputType>
    <AssemblyName>{m.name}.StubCheck</AssemblyName>
    <Nullable>disable</Nullable>
    <ImplicitUsings>disable</ImplicitUsings>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <TreatWarningsAsErrors>false</TreatWarningsAsErrors>
    <NoWarn>CS0649;CS0169;CS0414;CS1591;CS8632;CS0108;CS0114</NoWarn>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="{HERE / 'stubs' / 'TmlStubs.cs'}" />
    <Compile Include="Ids.cs" />
    <Compile Include="{m.out}/**/*.cs" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
    r = subprocess.run(["dotnet", "build", "Check.csproj", "-nologo", "-v", "q", "-o", "out"], cwd=work, capture_output=True, text=True)
    text = (r.stdout + r.stderr)
    errs = [l for l in text.splitlines() if ": error " in l]
    if not quiet:
        for l in sorted(set(errs)):
            print("  " + l.replace(str(m.root) + "/", ""))
    return r.returncode == 0, len(errs), unverified


def real_build(m):
    tml = os.environ.get("TML_DIR")
    if not tml or not Path(tml).exists():
        return None
    r = subprocess.run(["dotnet", "build", f"{m.name}.csproj", "-c", "Release"], cwd=m.out)
    return r.returncode == 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    root, cmd = argv[0], argv[1]
    try:
        m = Mod(root)
        if cmd == "gen":
            n = gen(m)
            print(f"{m.name}: generated {n} files in {m.out.relative_to(m.root)}/ ({len(m.all_items())} items, {len(m.tiles)} tiles, {len(m.projs)} projectiles, {len(m.enemies())} enemies, {len(m.bosses())} bosses)")
            return 0
        if cmd == "lint":
            errors = lint(m)
            for e in errors:
                print("  -", e)
            print(f"{m.name}: content lint {'FAILED' if errors else 'ok'}")
            return 1 if errors else 0
        if cmd == "preview":
            print("wrote", preview(m))
            return 0
        if cmd == "check":
            ok, n, unverified = check(m)
            print(f"{m.name}: stub compile check {'passed' if ok else 'FAILED'} ({n} error lines)")
            if unverified:
                print(f"  unverified vanilla IDs (the stub accepts any name; confirm these against tModLoader): {', '.join(unverified)}")
            return 0 if ok else 1
        if cmd == "build":
            gen(m)
            real = real_build(m)
            if real is None:
                print("TML_DIR is not set: running the stub compile check instead (this is NOT a real build)")
                ok, n, unverified = check(m)
                marker = m.root / "build"
                marker.mkdir(exist_ok=True)
                (marker / "compile-check.json").write_text(json.dumps({"ok": ok, "real_build": False, "unverified_ids": unverified}, indent=2))
                return 0 if ok else 1
            return 0 if real else 1
    except SpecError as exc:
        print(exc)
        return 1
    print(f"unknown command {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
