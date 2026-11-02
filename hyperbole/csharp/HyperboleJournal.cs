// Hyperbole — écrivain de journal pour un jeu ou des bots en C# (.NET 8+, Godot .NET, serveur).
// Copier ce fichier dans le projet. Contrat : Super_Toolbox/hyperbole/docs/PROTOCOLE.md.
// Lire le contrat de Mr. Popo : var c = HyperboleContract.Load(path) (chemin : argument --hyperbole=… ou variable
// d'environnement HYPERBOLE_CHAMBER). Écrire : using var j = new HyperboleJournal(c.Journal, c.World, () => tempsDeJeu);
// j.Write("death", ("bot", nom), ("cause", "wyrm"), ("pos", new[] { x, y })). Le fichier stop : c.StopRequested.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Hyperbole;

public sealed class HyperboleContract
{
    public required JsonObject Raw { get; init; }
    public string World => (string)Raw["world"]!;
    public long Seed => (long)Raw["seed"]!;
    public string Mode => (string)Raw["mode"]!;
    public string Journal => (string)Raw["journal"]!;
    public string StopFile => (string)Raw["stop_file"]!;
    public double WallSeconds => (double?)Raw["wall_seconds"] ?? 600;
    public double? GameSecondsMax => (double?)Raw["game_seconds_max"];
    public JsonNode? Speed => Raw["speed"];
    public JsonArray Lobby => Raw["lobby"]!.AsArray();
    public JsonObject Params => Raw["params"]?.AsObject() ?? new JsonObject();
    public bool StopRequested => File.Exists(StopFile);

    /// <summary>Le contrat donné par Mr. Popo, ou null si on n'est pas dans une chambre (le jeu tourne normalement).</summary>
    public static HyperboleContract? Load(string[]? args = null)
    {
        string? path = null;
        foreach (var a in args ?? Environment.GetCommandLineArgs())
            if (a.StartsWith("--hyperbole=", StringComparison.Ordinal)) path = a["--hyperbole=".Length..];
        path ??= Environment.GetEnvironmentVariable("HYPERBOLE_CHAMBER");
        if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;
        return new HyperboleContract { Raw = JsonNode.Parse(File.ReadAllText(path))!.AsObject() };
    }
}

/// <summary>Un événement JSON par ligne. Un seul écrivain par fichier ; thread-safe pour plusieurs bots d'un processus.</summary>
public sealed class HyperboleJournal : IDisposable
{
    static readonly JsonSerializerOptions Json = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
    readonly StreamWriter _w;
    readonly Func<double> _tGame;
    readonly Stopwatch _wall = Stopwatch.StartNew();
    readonly object _lock = new();
    public string World { get; }

    public HyperboleJournal(string path, string world, Func<double> tGame)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        _w = new StreamWriter(path, append: true, new UTF8Encoding(false)) { AutoFlush = false };
        World = world;
        _tGame = tGame;
    }

    public void Write(string kind, params (string Key, object? Value)[] data)
    {
        var ev = new Dictionary<string, object?>
        {
            ["t_game"] = Math.Round(_tGame(), 3), ["t_wall"] = Math.Round(_wall.Elapsed.TotalSeconds, 3),
            ["world"] = World, ["kind"] = kind,
        };
        foreach (var (k, v) in data) if (v is not null) ev[k] = v;
        var line = JsonSerializer.Serialize(ev, Json);
        lock (_lock) _w.WriteLine(line);
    }

    public void Flush() { lock (_lock) _w.Flush(); }
    public void Dispose() { lock (_lock) _w.Dispose(); }
}
