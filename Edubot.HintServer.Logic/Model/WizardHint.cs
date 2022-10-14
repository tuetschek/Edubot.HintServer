using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Edubot.HintServer.Logic.Model
{
    /// <summary>
    /// Wizard hint.
    /// </summary>
    public class WizardHint
    {
        /// <summary>
        /// Recommended field.
        /// </summary>
        public string? Field { get; set; }

        /// <summary>
        /// Recommended values.
        /// </summary>
        public List<string>? Value { get; set; }
    }
}
