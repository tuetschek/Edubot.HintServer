using Edubot.HintServer.Logic;
using Edubot.HintServer.Logic.Model;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Edubot.HintServer.Web.Controllers
{
    /// <summary>
    /// Main API controller.
    /// </summary>
    [Route("api")]
    [ApiController]
    public class EdubotApiController : ControllerBase
    {
        /// <summary>
        /// Methods for hinting.
        /// </summary>
        private readonly HintGenerationManager hintGenerationManager;

        /// <summary>
        /// Constructor.
        /// </summary>
        /// <param name="hintGenerationManager">Hint generation methods.</param>
        public EdubotApiController( HintGenerationManager hintGenerationManager)
        {
            this.hintGenerationManager = hintGenerationManager;
        }

        /// <summary>
        /// Hinting.
        /// </summary>
        /// <param name="request">Hint request.</param>
        /// <returns>Hint response.</returns>
        [HttpPost]
        [Route("hint")]
        public HintGenerationResponse Search(HintGenerationRequest request)
        {
            return hintGenerationManager.GenerateHintsForQuery(request);
        }
    }
}
