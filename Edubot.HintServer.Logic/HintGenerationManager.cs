using Edubot.HintServer.Logic.Model;
using SolrNet;

namespace Edubot.HintServer.Logic
{
    /// <summary>
    /// Generator of hints.
    /// </summary>
    public class HintGenerationManager
    {
        public readonly ISolrOperations<GeneralDocument> solr;
        private readonly HintSystemConfiguration hintConfiguration;

        public HintGenerationManager(
            ISolrOperations<GeneralDocument> solr,
            HintSystemConfiguration hintConfiguration
        )
        {
            this.solr = solr;
            this.hintConfiguration = hintConfiguration;
        }

        public HintGenerationResponse GenerateHintsForQuery(HintGenerationRequest request)
        {
            var solrQuery = GenerateQuery(request);

            var results = solr.Query(solrQuery, hintConfiguration.QueryOptions);

            var response = new HintGenerationResponse();

            GenerateSearchHints(results, request, response);
            GenerateWizardHints(results, request, response);

            return response;
        }

        private ISolrQuery GenerateQuery(HintGenerationRequest request)
        {
            var subQueries = new List<AbstractSolrQuery>();

            var textValue = request?.TextValue;
            if (textValue != null)
            {
                var textSubQueries = new List<AbstractSolrQuery>();

                foreach (var (textField, coeff) in hintConfiguration.TextFields)
                {
                    textSubQueries.Add(new SolrQueryByField(textField, textValue) { Quoted = false }.Boost(coeff));
                }

                subQueries.Add(new SolrMultipleCriteriaQuery(textSubQueries, "OR"));
            }

            var notRelevantEnums = request?.NotRelevantValues ?? new HashSet<string>();
            var selectedEnumValues = request?.EnumValues ?? new Dictionary<string, List<string>>();

            foreach (var (field, values) in selectedEnumValues)
            {
                if (values == null || !values.Any() || notRelevantEnums.Contains(field) || !hintConfiguration.EnumFields.Contains(field))
                {
                    continue;
                }

                subQueries.Add(new SolrQueryInList(field, values));
            }

            return subQueries.Any() ? new SolrMultipleCriteriaQuery(subQueries, "AND") : SolrQuery.All;
        }

        private void GenerateWizardHints(SolrQueryResults<GeneralDocument> results, HintGenerationRequest request, HintGenerationResponse response)
        {
            var total = results.NumFound;
            var stats = results.Stats[hintConfiguration.IdField].FacetResults;

            var bestScore = long.MaxValue;

            foreach (var field in hintConfiguration.WizardHintFields)
            {
                if (!stats.TryGetValue(field, out var fieldStats)
                    || (request?.NotRelevantValues?.Contains(field) ?? false)
                    || (request?.EnumValues?.ContainsKey(field) ?? false)
                )
                {
                    continue;
                }

                var remaining = total - fieldStats.Values.Sum(x => x.Count);
                var score = fieldStats.Values.Sum(x => x.Count * x.Count) + remaining * remaining;

                if (score < bestScore)
                {
                    bestScore = score;
                    response.WizardHints = new List<WizardHint>
                    {
                        new WizardHint
                        {
                            Field = field,
                            Value = fieldStats.OrderByDescending(x => x.Value.Count).Where(x => x.Value.Count > 0).Select(x => x.Key).ToList(),
                        }
                    };
                }
            }
        }

        private void GenerateSearchHints(SolrQueryResults<GeneralDocument> results, HintGenerationRequest request, HintGenerationResponse response)
        {
            var count = results.NumFound;
            var stats = results.Stats[hintConfiguration.IdField].FacetResults;

            var hintQueue = new SortedList<decimal, Dictionary<string, string>>();

            foreach (var field in hintConfiguration.SearchHintFields)
            {
                if (!stats.TryGetValue(field, out var fieldStats)
                    || (request?.NotRelevantValues?.Contains(field) ?? false)
                    || (request?.EnumValues?.ContainsKey(field) ?? false)
                )
                {
                    continue;
                }

                foreach (var value in fieldStats.Keys)
                {
                    var score = (decimal)fieldStats[value].Count;

                    while (hintQueue.ContainsKey(score))
                    {
                        score += new decimal(0.1);
                    }

                    hintQueue.Add(score, new Dictionary<string, string> { { field, value } });
                }
            }

            if (hintQueue.Any())
            {
                response.SearchHints = hintQueue.Take(5).Select(x => x.Value).ToList();
            }
        }
    }
}
