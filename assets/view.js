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
                                    $("#deployment").html('<div><button onclick="stop_deployment(' + String(challenge_id) + ',' + String(user_id) + ',' + '\'' + String(nonce) + '\'' +')" class="btn btn-outline-secondary"><i class="fas fa-play"></i> Stop Challenge</button><div><div class="table-responsive" id="deployinfo"></div>');
                                    create_table(data);
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

function create_table(data) {
    // Create table from info endpoint.
    for (let k in data) {
        // For every key in dictionary from data.
        if (k === "nodes") {
            // If key is nodes create table
            var div = document.getElementById('deployinfo');
            var nodes = document.createElement('table');
            nodes.classList.add("table");
            nodes.id = "nodestable";

            // Insert thead
            var thead = document.createElement('thead');
            thead.classList.add("thead-light");

            // Insert tbody
            var tbody = document.createElement('tbody');

            // Insert tablerow for thead and create name cell
            var tr = document.createElement('tr');
            var name = document.createElement('th');
            var nametext = document.createTextNode("Name");
            name.setAttribute("data-field", "name");
            name.appendChild(nametext);

            // Insert addresses cell
            var addresses = document.createElement('th');
            var addresstext = document.createTextNode("Addresses");
            addresses.setAttribute("data-field", "addresses");
            addresses.appendChild(addresstext);

            // Add cells and row to thead. Add thead to table.
            tr.appendChild(name);
            tr.appendChild(addresses);
            thead.appendChild(tr);
            nodes.appendChild(thead);

            // Insert tbody
            for (const node of data[k]) {
                var tr = document.createElement('tr');

                // Insert name cell
                var name = document.createElement('td');
                var nametext = document.createTextNode(node["name"]);
                name.appendChild(nametext);

                // Insert addresses cell
                var addresses = document.createElement('td');
                var addresstext = document.createTextNode(JSON.stringify(node["addresses"]));
                addresses.appendChild(addresstext);

                // Add cells and row to tbody.
                tr.appendChild(name);
                tr.appendChild(addresses);
                tbody.appendChild(tr);
            };

            // Add tbody to table. Add table to div.
            nodes.appendChild(tbody);
            div.appendChild(nodes);
        };
        if (k === "services") {
            // If key is services create table
            var div = document.getElementById('deployinfo');
            var services = document.createElement('table');
            services.classList.add("table");
            services.id = "servicestable";

            // Insert thead
            var thead = document.createElement('thead');
            thead.classList.add("thead-light");

            // Insert tbody
            var tbody = document.createElement('tbody');

            // Insert tablerow for thead and create name cell
            var tr = document.createElement('tr');
            var name = document.createElement('th');
            var nametext = document.createTextNode("Name");
            name.setAttribute("data-field", "name");
            name.appendChild(nametext);

            // Insert ports cell
            var port = document.createElement('th');
            var porttext = document.createTextNode("Ports");
            port.setAttribute("data-field", "ports");
            port.appendChild(porttext);

            // Insert clusterip cell
            var clusterip = document.createElement('th');
            var iptext = document.createTextNode("ClusterIP");
            clusterip.setAttribute("data-field", "clusterIP");
            clusterip.appendChild(iptext);

            // Add cells and row to thead. Add thead to table.
            tr.appendChild(name);
            tr.appendChild(clusterip);
            tr.appendChild(port);
            thead.appendChild(tr);
            services.appendChild(thead);

            // Insert tbody
            for (const service of data[k]) {
                var tr = document.createElement('tr');

                // Insert name cell
                var name = document.createElement('td');
                var nametext = document.createTextNode(service["name"]);
                name.appendChild(nametext);

                // Insert port cell
                var port = document.createElement('td');
                var porttext = document.createTextNode(JSON.stringify(service["ports"]));
                port.appendChild(porttext);

                // Insert clusterip cell
                var clusterip = document.createElement('td');
                var iptext = document.createTextNode(service["clusterIP"]);
                clusterip.appendChild(iptext);

                // Add cells and row to tbody.
                tr.appendChild(name);
                tr.appendChild(clusterip);
                tr.appendChild(port);
                tbody.appendChild(tr);
            };

            // Add tbody to table. Add table to div.
            services.appendChild(tbody);
            div.appendChild(services);
        };
    };    
};
