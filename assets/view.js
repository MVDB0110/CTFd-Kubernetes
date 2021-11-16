CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();


CTFd._internal.challenge.preRender = function () { }

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
}


CTFd._internal.challenge.postRender = function () { }


CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var submission = CTFd.lib.$('#challenge-input').val()
    var user_id = CTFd.lib.$('#user-id').val()
    var nonce = CTFd.lib.$('#nonce').val()

    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview) {
        params['preview'] = true
    }

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.data.status === 429) {
            // User was ratelimited but process response
            return response
        }
        if (response.data.status === 403) {
            // User is not logged in or CTF is paused.
            return response
        }
        if (response.data.status == "correct") {
            stop_deployment(challenge_id, user_id, nonce);
            return response
        }
        if (response.data.status == "already_solved") {
            stop_deployment(challenge_id, user_id, nonce);
            return response
        }
        return response
    })
};

function start_deployment(challenge_id, user_id, nonce) {
    $('#deployment').html('<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i></div>');
    json_body = { "challenge_id": challenge_id, "user_id": user_id }
    headers = { "CSRF-Token": nonce, 'Content-Type': 'application/json' }

    $.ajax({
        type: 'POST',
        url: '/kubernetes/deploy/namespace',
        data: JSON.stringify(json_body),
        headers: headers,
        success: function (data) {
            $.ajax({
                type: 'POST',
                url: '/kubernetes/deploy/rbac',
                data: JSON.stringify(json_body),
                headers: headers,
                success: function (data) {

                    json_body["role_name"] = data["role_name"];

                    $.ajax({
                        type: 'POST',
                        url: '/kubernetes/deploy/job',
                        data: JSON.stringify(json_body),
                        headers: headers,
                        success: function (data) {
                            
                            $.ajax({
                                type: 'POST',
                                url: '/kubernetes/deploy/info',
                                data: JSON.stringify(json_body),
                                headers: headers,
                                success: function (data) {
                                    $("#deployment").html('<button onclick="stop_deployment(' + String(challenge_id) + ',' + String(user_id) + ',' + '\'' + String(nonce) + '\'' +')" class="btn btn-outline-secondary"><i class="fas fa-play"></i> Stop Challenge</button>');
                                    var myWindow = window.open("", "challenge-" + json_body["challenge_id"], "width=800,height=600");
                                    myWindow.document.write("<pre>" + JSON.stringify(data, undefined, 4) + "</pre>");
                                },
                                error: function (data) { $('#deployment').html('<div class="text-center">Cannot get your challenge environment information.</div>'); return },
                                dataType: 'json'
                            });
                        },
                        error: function (data) { $('#deployment').html('<div class="text-center">Cannot deploy the challenge deployment container.</div>'); return },
                        dataType: 'json'
                    });
                },
                error: function (data) { $('#deployment').html('<div class="text-center">Cannot deploy rbac in namespace.</div>'); return },
                dataType: 'json'
            });
        },
        error: function (data) { $('#deployment').html('<div class="text-center">Cannot deploy your challenge namespace.</div>'); return },
        dataType: 'json'
    });

};

function stop_deployment(challenge_id, user_id, nonce) {
    json_body = { "challenge_id": challenge_id, "user_id": user_id }
    headers = { "CSRF-Token": nonce, 'Content-Type': 'application/json' }
    $.ajax({
        type: 'POST',
        url: '/kubernetes/destroy',
        data: JSON.stringify(json_body),
        success: function (data) { $('#deployment').html('<div class="text-center">Destroyed your challenge environment.</div>'); },
        error: function (data) { $('#deployment').html('<div class="text-center">Cannot destroy your challenge environment.</div>'); },
        headers: headers,
        dataType: 'json'
    });
};