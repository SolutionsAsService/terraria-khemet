namespace Khemet.Systems
{
    /// <summary>The GrandPyramid blueprint, drawn one character per tile and run-length encoded (generated from content/structures.json by shadw-mod; do not edit).
    /// 121 wide, 94 tall, the ground at row 60.</summary>
    public static class GrandPyramidBlueprint
    {
        public const int Width = 121;
        public const int Height = 94;
        public const int GroundRow = 60;

        public static readonly string[] Rows = new string[]
        {
            " 58G5 58",
            " 58G5 58",
            " 56G9 56",
            " 56G9 56",
            " 54G13 54",
            " 54G13 54",
            " 52B17 52",
            " 52B17 52",
            " 50B21 50",
            " 50B21 50",
            " 48B25 48",
            " 48B25 48",
            " 46G3B23G3 46",
            " 46G3B23G3 46",
            " 44B33 44",
            " 44B33 44",
            " 42B7.23B7 42",
            " 42B7.23B7 42",
            " 40B7.27B7 40",
            " 40B7.27B7 40",
            " 38B8.1T1.25T1.1B8 38",
            " 38B8.29B8 38",
            " 36B10.29B10 36",
            " 36B10.29B10 36",
            " 34G3B9.29B9G3 34",
            " 34G3B9.29B9G3 34",
            " 32B14.29B14 32",
            " 32B14.1T1.3C1c1.15C1c1.3T1.1B14 32",
            " 30B16.5c2.15c2.5B16 30",
            " 30B16L11p7L11B16 30",
            " 28B18.29B18 28",
            " 28B18.29B18 28",
            " 26B20.29B20 26",
            " 26B20.29B20 26",
            " 24B22.1T1.17p6.2T1.1B22 24",
            " 24B22.29B22 24",
            " 22G3B21.29B21G3 22",
            " 22G3B21.29B21G3 22",
            " 20B26.29B26 20",
            " 20B26.4p6.19B26 20",
            " 18B28.29B28 18",
            " 18B28.1T1.25T1.1B28 18",
            " 16B30.29B30 16",
            " 16B30.29B30 16",
            " 14B32.19p6.4B32 14",
            " 14B32.29B32 14",
            " 10.4B1.4B1.4B1.4B1.1B15.29B34 12",
            " 10.4B1.4B1.4B1.4B1.1B15.29B34 12",
            " 10.4B1.4B1.4B1.4B1.1B15.1T1.25T1.1B33G3 10",
            " 10.3T1.4T1.4T1.7B15.4p6.19B33G3 10",
            " 8B2.21B15.29B38 8",
            " 8B2.21B15.29B38 8",
            " 6B4.21B15.29B40 6",
            "H10.21B15.29B40 6",
            ".65p6.4B42 4",
            ".34T1.5T1.6T1.25T1.1B42 4",
            ".75B44 2",
            ".75B44 2",
            ".12C1c1.14C1c1.45B46",
            ".12c2.14c2.3K8.34B46",
            "B59.3B59",
            "B59.3B59",
            " 1B58.3B58 1",
            " 1B58.3B58 1",
            " 2B57.3B57 2",
            " 2B57.3B57 2",
            " 3B56.3B56 3",
            " 3B56.3B56 3",
            " 4B55.3B55 4",
            " 4B32H23.3H23B32 4",
            " 5B31.4B1.7B1.7B1.7B1.7B1.7B1.4B31 5",
            " 5B31.4B1.7B1.7B1.7B1.7B1.7B1.4B31 5",
            " 6B2.16B12.4B1.7B1.7B1.7B1.7B1.7B1.4B12.16B2 6",
            " 6B2.16B12.3T1.7T1.7T1.7T1.7T1.7T1.5B12.16B2 6",
            " 7B1.16B12.49B12.16B1 7",
            " 7B1.3T1.4T1.7B12.49B12.3T1.4T1.7B1 7",
            " 8.16B12.49B12.16 8",
            " 8.16B12.49B12.16 8",
            " 8.16B12.49B12.16 8",
            " 8.16B12.49B12.16 8",
            " 8.16B12.49B12.16 8",
            " 8.16B12.49B12.16 8",
            " 8.105 8",
            " 8.105 8",
            " 8.32B1.7B1.7B1.7B1.7B1.7B1.32 8",
            " 8.9C1c1.21B1.7B1.1C1c1.4B1.7B1.3C1c1.2B1.7B1.19C1c1.3C1c1.6 8",
            " 8.9c2.8K6.7B1.7B1.1c2.4B1.7B1.3c2.2B1.7B1.7K6.6c2.3c2.6 8",
            " 13B23L49B23 13",
            " 14B93 14",
            " 14B93 14",
            " 15B91 15",
            " 15B91 15",
            " 16B89 16",
            " 16B89 16"
        };

        /// <summary>Row r as one character per tile.</summary>
        public static string Decode(int r)
        {
            string s = Rows[r];
            var sb = new System.Text.StringBuilder();
            int i = 0;
            while (i < s.Length)
            {
                char c = s[i++];
                int n = 0;
                while (i < s.Length && char.IsDigit(s[i]))
                {
                    n = n * 10 + (s[i++] - '0');
                }
                sb.Append(c, n);
            }
            return sb.ToString();
        }
    }
}
