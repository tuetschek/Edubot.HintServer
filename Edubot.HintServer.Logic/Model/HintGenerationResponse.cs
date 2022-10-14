using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Edubot.HintServer.Logic.Model
{
    /// <summary>
    /// Response with generated hints.
    /// </summary>
    public class HintGenerationResponse
    {
        /// <summary>
        /// Hints for wizard. Each item is a separate field.
        /// </summary>
        public List<WizardHint>? WizardHints { get; set; }

        /// <summary>
        /// Hints for search. Each item is a dictionary (key: field, value: value of field).
        /// </summary>
        public List<Dictionary<string, string>>? SearchHints { get; set; }
    }
}
