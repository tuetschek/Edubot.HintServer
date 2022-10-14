using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Edubot.HintServer.Logic.Model
{
    /// <summary>
    /// Request for hint generation.
    /// </summary>
    public class HintGenerationRequest
    {
        /// <summary>
        /// Text value for search.
        /// </summary>
        public string? TextValue { get; set; }

        /// <summary>
        /// Enum value for search.
        /// </summary>
        public Dictionary<string, List<string>>? EnumValues { get; set; }

        /// <summary>
        /// Not relevant values for search.
        /// </summary>
        public HashSet<string>? NotRelevantValues { get; set; }
    }
}
