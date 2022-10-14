using Edubot.HintServer.Logic;
using Edubot.HintServer.Logic.Model;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc.Formatters;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using SolrNet;
using SolrNet.Impl;
using SolrNet.Impl.ResponseParsers;
using SolrNet.Utils;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection.PortableExecutable;
using System.Runtime.CompilerServices;
using System.Xml.Linq;
using System.Xml.XPath;

var solrUrl = Environment.GetEnvironmentVariable("APP_URL_SOLR") ?? string.Empty;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddSignalR(e =>
{
    e.MaximumReceiveMessageSize = 102400000;
});
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();

HintSystemConfiguration hintConfig = LoadHintConfiguationFromConfig(builder.Configuration);

builder.Services.AddSingleton<HintSystemConfiguration>((x) => hintConfig);
builder.Services.AddScoped<HintGenerationManager>();

builder.Services.AddSolrNet<GeneralDocument>(solrUrl);
var invalidReponseParser = builder.Services.First(x => x.ServiceType.Equals(typeof(ISolrAbstractResponseParser<>)) && x.Lifetime == ServiceLifetime.Transient);
builder.Services.Remove(invalidReponseParser);
builder.Services.AddTransient(typeof(ISolrAbstractResponseParser<>), typeof(FixedDefaultResponseParser<>));

builder.Services.AddControllers();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
}

app.MapControllers();

app.UseSwagger();
app.UseSwaggerUI();

app.UseStaticFiles();

app.UseRouting();

app.MapBlazorHub();
app.MapFallbackToPage("/_Host");

app.Run();


HintSystemConfiguration LoadHintConfiguationFromConfig(Microsoft.Extensions.Configuration.ConfigurationManager configuration)
{
    if (configuration == null)
    {
        throw new ArgumentNullException("AppSettings is missing.");
    }

    var hintConfiguration = LoadAndValidateSectionFromRoot("HintConfiguration", configuration);

    var boostField = LoadAndValidateString("BoostField", hintConfiguration);
    var idField = LoadAndValidateString("IdField", hintConfiguration);

    var textFields = new Dictionary<string, double>();

    foreach (var textFieldConfiguration in LoadAndValidateSection("TextFields", hintConfiguration).GetChildren())
    {
        var title = LoadAndValidateString("Title", textFieldConfiguration);
        var boost = LoadAndValidateDouble("Boost", textFieldConfiguration);

        if (textFields.ContainsKey(title))
        {
            throw new ArgumentException($"Title \"{title}\" in TextFields is specified more than once.");
        }

        textFields.Add(title, boost);
    }

    if (textFields.Count == 0)
    {
        throw new ArgumentException("TextFields in HintConfiguration section in AppSettings is missing or empty.");
    }

    var enumFields = LoadAndValidateStringArrayToHashSet("EnumFields", hintConfiguration);
    var wizardHintFields = LoadAndValidateStringArrayToHashSet("WizardHintFields", hintConfiguration);
    var searchHintFields = LoadAndValidateStringArrayToHashSet("SearchHintFields", hintConfiguration);

    return new HintSystemConfiguration(textFields, enumFields, wizardHintFields, searchHintFields, boostField, idField);
}

IConfigurationSection LoadAndValidateSectionFromRoot(string key, IConfiguration root)
{
    var section = root.GetSection(key);

    if (section == null)
    {
        throw new ArgumentNullException($"{key} is missing in application configuration.");
    }

    return section;
}

IConfigurationSection LoadAndValidateSection(string key, IConfigurationSection parent)
{
    var section = parent.GetSection(key);

    if (section == null)
    {
        throw new ArgumentNullException($"{key} is missing in {parent.Key}.");
    }

    return section;
}

string LoadAndValidateString(string key, IConfigurationSection parent)
{
    var value = parent.GetValue<string>(key);

    if (value == null)
    {
        throw new ArgumentNullException($"{key} is missing in {parent.Key}.");
    }

    return value;
}

double LoadAndValidateDouble(string key, IConfigurationSection parent)
{
    var value = parent.GetValue<double?>(key);

    if (value == null)
    {
        throw new ArgumentNullException($"{key} is missing or invalid in {parent.Key}.");
    }

    return value.Value;
}

HashSet<string> LoadAndValidateStringArrayToHashSet(string key, IConfigurationSection parent)
{
    var result = new HashSet<string>();

    var subsection = LoadAndValidateSection(key, parent);

    foreach(var child in subsection.GetChildren())
    {
        var field = child.Value;

        if (!result.Add(field))
        {
            throw new ArgumentException($"Field \"{field}\" in {key} is specified more than once.");
        }
    }

    if (result.Count == 0)
    {
        throw new ArgumentNullException($"{key} is empty in {parent.Key}.");
    }

    return result;
}

public class FixedDefaultResponseParser<T> : ISolrAbstractResponseParser<T>
{
    private readonly AggregateResponseParser<T> parser;

    public FixedDefaultResponseParser(ISolrDocumentResponseParser<T> docParser)
    {
        parser = new AggregateResponseParser<T>(new ISolrAbstractResponseParser<T>[] {
                new ResultsResponseParser<T>(docParser),
                new HeaderResponseParser<T>(),
                new FacetsResponseParser<T>(),
                new HighlightingResponseParser<T>(),
                new MoreLikeThisResponseParser<T>(docParser),
                new SpellCheckResponseParser<T>(),
                new FixedResponseParser<T>(),
                new CollapseResponseParser<T>(),
                new GroupingResponseParser<T>(docParser),
                new CollapseExpandResponseParser<T>(docParser),
                new ClusterResponseParser<T>(),
                new TermsResponseParser<T>(),
                new MoreLikeThisHandlerMatchResponseParser<T>(docParser),
                new InterestingTermsResponseParser<T>(),
                new TermVectorResultsParser<T>(),
                new DebugResponseParser<T>()
            });
    }

    /// <inheritdoc />
    public void Parse(XDocument xml, AbstractSolrQueryResults<T> results)
    {
        parser.Parse(xml, results);
    }
}

/// <summary>
/// Parses stats results from a query response
/// </summary>
/// <typeparam name="T">Document type</typeparam>
public class FixedResponseParser<T> : ISolrResponseParser<T>
{
    private class TypedStatsResult : ITypedStatsResult<string>
    {
        public string Min { get; set; }
        public string Max { get; set; }
        public string Sum { get; set; }
        public string SumOfSquares { get; set; }
        public string Mean { get; set; }
        public string StdDev { get; set; }
    }

    /// <inheritdoc />
    public void Parse(XDocument xml, AbstractSolrQueryResults<T> results)
    {
        results.Switch(query: r => Parse(xml, r),
            moreLikeThis: F.DoNothing);
    }

    /// <inheritdoc />
    public void Parse(XDocument xml, SolrQueryResults<T> results)
    {
        var statsNode = xml.XPathSelectElement("response/lst[@name='stats']");
        if (statsNode != null)
            results.Stats = ParseStats(statsNode, "stats_fields");
    }

    /// <summary>
    /// Parses the stats results and uses recursion to get any facet results
    /// </summary>
    /// <param name="node"></param>
    /// <param name="selector">Start with 'stats_fields'</param>
    /// <returns></returns>
    public Dictionary<string, StatsResult> ParseStats(XElement node, string selector)
    {
        var d = new Dictionary<string, StatsResult>();
        var mainNode = node.XPathSelectElement(string.Format("lst[@name='{0}']", selector));
        foreach (var n in mainNode.Elements())
        {
            var name = n.Attribute("name")?.Value ?? string.Empty;
            d[name] = ParseStatsNode(n);
        }

        return d;
    }

    public IDictionary<string, Dictionary<string, StatsResult>> ParseFacetNode(XElement node)
    {
        var r = new Dictionary<string, Dictionary<string, StatsResult>>();
        foreach (var n in node.Elements())
        {
            var facetName = n.Attribute("name").Value;
            r[facetName] = ParseStats(n.Parent, facetName);
        }
        return r;
    }

    /// <summary>
    /// Parses percentiles node.
    /// </summary>
    /// <param name="node">Percentile node.</param>
    /// <returns></returns>
    public IDictionary<double, double> ParsePercentilesNode(XElement node)
    {
        var r = new Dictionary<double, double>();

        foreach (var n in node.Elements())
        {
            var percentile = Convert.ToDouble(n.Attribute("name").Value, CultureInfo.InvariantCulture);
            r.Add(percentile, GetDoubleValue(n));
        }
        return r;
    }

    public StatsResult ParseStatsNode(XElement node)
    {
        var typedStatsResult = new TypedStatsResult();
        var r = new StatsResult(typedStatsResult);
        foreach (var statNode in node.Elements())
        {
            var name = statNode.Attribute("name").Value;
            var value = statNode.Name.LocalName.Equals("null") ? null : statNode.Value;
            switch (name)
            {
                case "min":
                    r.Min = GetDoubleValue(statNode);
                    typedStatsResult.Min = value;
                    break;
                case "max":
                    r.Max = GetDoubleValue(statNode);
                    typedStatsResult.Max = value;
                    break;
                case "sum":
                    r.Sum = GetDoubleValue(statNode);
                    typedStatsResult.Sum = value;
                    break;
                case "sumOfSquares":
                    r.SumOfSquares = GetDoubleValue(statNode);
                    typedStatsResult.SumOfSquares = value;
                    break;
                case "mean":
                    r.Mean = GetDoubleValue(statNode);
                    typedStatsResult.Mean = value;
                    break;
                case "stddev":
                    r.StdDev = GetDoubleValue(statNode);
                    typedStatsResult.StdDev = value;
                    break;
                case "count":
                    r.Count = Convert.ToInt64(statNode.Value, CultureInfo.InvariantCulture);
                    break;
                case "missing":
                    r.Missing = Convert.ToInt64(statNode.Value, CultureInfo.InvariantCulture);
                    break;
                case "percentiles":
                    r.Percentiles = ParsePercentilesNode(statNode);
                    break;
                default:
                    r.FacetResults = ParseFacetNode(statNode);
                    break;
            }
        }
        return r;
    }

    private static double GetDoubleValue(XElement statNode)
    {
        double parsedValue;
        if (!double.TryParse(statNode.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out parsedValue))
            parsedValue = double.NaN;
        return parsedValue;
    }
}