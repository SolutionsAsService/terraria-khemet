using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.Generation;
using Terraria.ID;
using Terraria.IO;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Khemet.Systems
{
    /// <summary>Adds GrandPyramid to world generation (site: desert) and stocks its chests by role. The layout is GrandPyramidBlueprint.</summary>
    public class GrandPyramidGenSystem : ModSystem
    {
        private static readonly int[][] ChestCells = new int[][]
        {
            new int[] { 12, 58 },
            new int[] { 28, 58 },
            new int[] { 100, 85 },
            new int[] { 105, 85 },
            new int[] { 17, 85 },
            new int[] { 50, 85 },
            new int[] { 68, 85 },
            new int[] { 68, 27 },
            new int[] { 51, 27 },
        };

        private static readonly string[] ChestRoles = new string[] { "gates", "gates", "vault", "vault", "crypt", "judgement", "judgement", "throne", "throne" };

        public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight)
        {
            int index = tasks.FindIndex(pass => pass.Name.Equals("Pyramids"));
            if (index == -1)
            {
                index = tasks.Count - 1;
            }
            tasks.Insert(index + 1, new PassLegacy("GrandPyramid", GenerateGrandPyramid));
        }

        private static int SurfaceY(int x)
        {
            for (int y = 60; y < (int)Main.worldSurface; y++)
            {
                Tile tile = Main.tile[x, y];
                if (tile.HasTile && Main.tileSolid[tile.TileType])
                {
                    return y;
                }
            }
            return -1;
        }

        private static bool IsSand(int type)
        {
            return type == TileID.Sand || type == TileID.HardenedSand || type == TileID.Sandstone;
        }

        private static void Put(Chest chest, ref int slot, int type, int stack)
        {
            if (slot < 40)
            {
                chest.item[slot].SetDefaults(type);
                chest.item[slot].stack = stack;
                slot++;
            }
        }

        private static void GenerateGrandPyramid(GenerationProgress progress, GameConfiguration configuration)
        {
            progress.Message = "Building GrandPyramid";
            int W = GrandPyramidBlueprint.Width;
            int H = GrandPyramidBlueprint.Height;
            int groundRow = GrandPyramidBlueprint.GroundRow;
            int bestX = -1;
            double bestScore = -1000.0;
            for (int attempt = 0; attempt < 400; attempt++)
            {
                int x0 = WorldGen.genRand.Next(Main.maxTilesX / 8, Main.maxTilesX * 7 / 8 - W);
                int sand = 0;
                int ground = 0;
                int count = 0;
                int minY = int.MaxValue;
                int maxY = 0;
                for (int x = x0; x < x0 + W; x += 3)
                {
                    int y = SurfaceY(x);
                    if (y < 0)
                    {
                        continue;
                    }
                    count++;
                    minY = Math.Min(minY, y);
                    maxY = Math.Max(maxY, y);
                    int t = Main.tile[x, y].TileType;
                    if (IsSand(t))
                    {
                        sand++;
                    }
                    else if (t == TileID.Grass || t == TileID.Dirt || t == TileID.Stone)
                    {
                        ground++;
                    }
                }
                if (count == 0)
                {
                    continue;
                }
                double score = sand / (double)count * 100.0 - (maxY - minY) * 1.5;
                if (score > bestScore)
                {
                    bestScore = score;
                    bestX = x0;
                }
            }
            if (bestX < 0)
            {
                return;
            }
            List<int> ys = new List<int>();
            for (int x = bestX; x < bestX + W; x += 2)
            {
                int y = SurfaceY(x);
                if (y > 0)
                {
                    ys.Add(y);
                }
            }
            ys.Sort();
            int groundLine = ys[ys.Count / 2];
            int top = groundLine - groundRow;
            for (int x = bestX; x < bestX + W; x++)
            {
                for (int y = top - 2; y < groundLine; y++)
                {
                    Main.tile[x, y].ClearEverything();
                }
                for (int y = groundLine; y < groundLine + 3; y++)
                {
                    WorldGen.PlaceTile(x, y, TileID.Sandstone, true, true);
                }
            }
            Dictionary<char, int> tiles = new Dictionary<char, int>();
            tiles['B'] = ModContent.TileType<Tiles.PharaohBrickTile>();
            tiles['G'] = ModContent.TileType<Tiles.GoldenSandstoneTile>();
            tiles['H'] = ModContent.TileType<Tiles.HieroglyphBrickTile>();
            tiles['L'] = ModContent.TileType<Tiles.LapisInlayTile>();
            for (int r = 0; r < H; r++)
            {
                progress.Set(r / (float)H);
                string row = GrandPyramidBlueprint.Decode(r);
                for (int c = 0; c < W; c++)
                {
                    char ch = row[c];
                    int x = bestX + c;
                    int y = top + r;
                    if (ch == ' ')
                    {
                        continue;
                    }
                    Tile tile = Main.tile[x, y];
                    tile.ClearEverything();
                    if (ch == '.' || ch == 'c' || ch == 'C' || ch == 'T' || ch == 'p' || ch == 'K' || ch == 'R')
                    {
                        tile.WallType = WallID.SandstoneBrick;
                    }
                    else if (ch == 'w')
                    {
                        tile.WallType = WallID.SandstoneBrick;
                    }
                    else
                    {
                        WorldGen.PlaceTile(x, y, tiles[ch], true, true);
                    }
                }
            }
            for (int r = 0; r < H; r++)
            {
                string row = GrandPyramidBlueprint.Decode(r);
                for (int c = 0; c < W; c++)
                {
                    int x = bestX + c;
                    int y = top + r;
                    switch (row[c])
                    {
                        case 'p':
                            WorldGen.PlaceTile(x, y, TileID.Platforms, true, true, -1, 0);
                            break;
                        case 'K':
                            WorldGen.PlaceTile(x, y, TileID.Spikes, true, true);
                            break;
                        case 'T':
                            WorldGen.PlaceTile(x, y, TileID.Torches, true, false, -1, 0);
                            break;
                    }
                }
            }
            for (int i = 0; i < ChestCells.Length; i++)
            {
                int cx = bestX + ChestCells[i][0];
                int cy = top + ChestCells[i][1];
                int index = WorldGen.PlaceChest(cx, cy, (ushort)TileID.Containers, false, 1);
                if (index < 0)
                {
                    continue;
                }
                Chest chest = Main.chest[index];
                int slot = 0;
                switch (ChestRoles[i])
                {
                case "gates":
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.GoldCoin, WorldGen.genRand.Next(1, 4)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.HealingPotion, WorldGen.genRand.Next(1, 4)); }
                    if (WorldGen.genRand.Next(2) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.SunstoneShard>(), WorldGen.genRand.Next(1, 4)); }
                    break;
                case "judgement":
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.SunstoneShard>(), WorldGen.genRand.Next(4, 10)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.GoldBar, WorldGen.genRand.Next(3, 8)); }
                    if (WorldGen.genRand.Next(7) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.ScarabCharm>(), WorldGen.genRand.Next(1, 2)); }
                    break;
                case "vault":
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.GoldCoin, WorldGen.genRand.Next(5, 13)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.GoldBar, WorldGen.genRand.Next(8, 17)); }
                    if (WorldGen.genRand.Next(2) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.CursedCartouche>(), WorldGen.genRand.Next(1, 2)); }
                    if (WorldGen.genRand.Next(4) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.Khopesh>(), WorldGen.genRand.Next(1, 2)); }
                    break;
                case "crypt":
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.Bone, WorldGen.genRand.Next(6, 15)); }
                    if (WorldGen.genRand.Next(3) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.ScarabCharm>(), WorldGen.genRand.Next(1, 2)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.HealingPotion, WorldGen.genRand.Next(1, 3)); }
                    break;
                case "throne":
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.CursedCartouche>(), WorldGen.genRand.Next(1, 2)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ItemID.GoldCoin, WorldGen.genRand.Next(8, 21)); }
                    if (WorldGen.genRand.Next(1) == 0) { Put(chest, ref slot, ModContent.ItemType<Items.SunstoneShard>(), WorldGen.genRand.Next(6, 13)); }
                    break;
                }
            }
            Systems.KhemetWorld.GrandPyramidArea = new Rectangle(bestX, top, W, H);
        }
    }
}
