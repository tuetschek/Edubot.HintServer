using SolrNet;
using SolrNet.Commands.Parameters;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Edubot.HintServer.Logic.Model
{
    /// <summary>
    /// Configuration of the hinting system.
    /// </summary>
    public class HintSystemConfiguration
    {
        /// <summary>
        /// Text fields and their coefficients.
        /// </summary>
        public Dictionary<string, double> TextFields { get; }

        /// <summary>
        /// Enumeration fields.
        /// </summary>
        public HashSet<string> EnumFields { get; }

        /// <summary>
        /// Fields for wizard hints.
        /// </summary>
        public HashSet<string> WizardHintFields { get; }

        /// <summary>
        /// Fields for search hints.
        /// </summary>
        public HashSet<string> SearchHintFields { get; }

        /// <summary>
        /// Field for query boost.
        /// </summary>
        public string BoostField { get; }

        /// <summary>
        /// Field for id.
        /// </summary>
        public string IdField { get; }

        /// <summary>
        /// Query options to be used by Solr.
        /// </summary>
        public QueryOptions QueryOptions { get; }

        /// <summary>
        /// Constructor.
        /// </summary>
        /// <param name="textFields">Text fields and their coefficients.</param>
        /// <param name="enumFields">Enumeration fields.</param>
        /// <param name="wizardHintFields">Fields for wizard hints.</param>
        /// <param name="searchHintFields">Fields for search hints.</param>
        /// <param name="boostField">Field for query boost.</param>
        /// <param name="idField">Field for id.</param>
        public HintSystemConfiguration(Dictionary<string, double> textFields, HashSet<string> enumFields, HashSet<string> wizardHintFields, HashSet<string> searchHintFields, string boostField, string idField)
        {
            TextFields = textFields;
            EnumFields = enumFields;
            WizardHintFields = wizardHintFields;
            SearchHintFields = searchHintFields;
            BoostField = boostField;
            IdField = idField;
            QueryOptions = CreateQueryOptions();
        }

        /// <summary>
        /// Compute query options.
        /// </summary>
        /// <returns>Query options to be used by Solr.</returns>
        private QueryOptions CreateQueryOptions()
        {
            var hintFields = WizardHintFields.Concat(SearchHintFields).Distinct().ToList();

            var extraParams = new List<KeyValuePair<string, string>>
            {
                new KeyValuePair<string, string>("qt", "dismax"),
                new KeyValuePair<string, string>("boost", BoostField),
                new KeyValuePair<string, string>("stats", "true"),
                new KeyValuePair<string, string>("stats.field", IdField),
            };

            extraParams.AddRange(hintFields.Select(field => new KeyValuePair<string, string>("stats.facet", field)));

            return new QueryOptions
            {
                StartOrCursor = new StartOrCursor.Start(0),
                Rows = 0,
                ExtraParams = extraParams,
                Fields = new string[0]
            };
        }
    }
}
