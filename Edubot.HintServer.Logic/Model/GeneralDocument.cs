using SolrNet.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Edubot.HintServer.Logic.Model
{
    /// <summary>
    /// Document used for Solr.
    /// </summary>
    public class GeneralDocument
    {
        /// <summary>
        /// All fields and values.
        /// </summary>
        [SolrField("*")]
        public IDictionary<string, object>? Fields { get; set; }
    }
}
