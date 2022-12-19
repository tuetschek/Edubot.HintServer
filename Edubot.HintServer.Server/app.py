from flask import Flask, jsonify, abort, render_template, request
import traceback
import hint_server.models as models
import hint_server.logic as logic
import hint_server.config as config

app = Flask(__name__)
app.json_encoder = models.ApiModelJSONEncoder

def errorPage(error: str, code: int):
    return render_template("error.html", error=error), code

@app.errorhandler(500)
def error500(error):
    return errorPage(error, 500)
    
@app.errorhandler(404)
def error404(error):
    return errorPage(error, 404)

@app.route("/api")
def api():
    if config.config is None: return errorPage(config.error_description, 500)
    return render_template("api.html")

@app.route("/search", methods = ["POST"])
def search():
    if config.config is None: return errorPage(config.error_description, 500)
    try:
        searchRequest = models.SearchRequest(request.get_json())
        searchResponse = logic.search(searchRequest, config.config)
        return jsonify(searchResponse)
    except:
        error = traceback.format_exc()
        print(error)
        return errorPage(error, 500)

@app.route("/hint", methods = ["POST"])
def hint():
    if config.config is None: return errorPage(config.error_description, 500)
    try:
        hintRequest = models.HintRequest(request.get_json())
        hintResponse = logic.hint(hintRequest, config.config)
        return jsonify(hintResponse)
    except:
        error = traceback.format_exc()
        print(error)
        return errorPage(error, 500)

#@app.route("/redirect", methods = ["POST"])
#def redirect():
#    if config.config is None:
#        return error(config.error_description, 500)
#    try:
#        redirectRequest = models.RedirectRequest(request.get_json())
#        redirectResponse = logic.redirect(redirectRequest, config.config)
#        return jsonify(redirectResponse);
#    except:
#        error = traceback.format_exc()
#        print(error)
#       return errorPage(error, 500)

@app.route("/", defaults={ "path": "" })
@app.route("/<path:path>")
def catch_all(path):
    return abort(404, "Not found")

if __name__ == '__main__':
    config.readAndValidateConfig("app.config.json")
    
    if False: # TEMP
        from waitress import serve
        serve(app, host="0.0.0.0", port=8000)
    else:
        app.run(host="0.0.0.0", port=8000)