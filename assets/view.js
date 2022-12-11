CTFd._internal.challenge.data=void 0,CTFd._internal.challenge.renderer=CTFd.lib.markdown(),CTFd._internal.challenge.preRender=function(){},CTFd._internal.challenge.postRender=function(){},CTFd._internal.challenge.render=function(e){return CTFd._internal.challenge.renderer.render(e)},CTFd._internal.challenge.submit=function(e){var n={},l={challenge_id:parseInt(CTFd.lib.$("#challenge-id").val()),submission:CTFd.lib.$("#challenge-input").val()};return e&&(n.preview=!0),CTFd.api.post_challenge_attempt(n,l).then(function(e){return 429===e.status?e:(e.status,e)})};

function initialize(challenge_id, user_id, nonce) {
    
    $('#deployment').html('<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i></div>');

    headers = { "CSRF-Token": nonce, 'Content-Type': 'application/json' };
    body = { "challenge_id": challenge_id, "user_id": user_id };

    $.ajax({
        type: 'GET',
        url: '/container_challenges/namespace?challenge_id=' + challenge_id + '&user_id=' + user_id,
        headers: headers,
        success: function (result) {
            found = result["found"]
            
            if (found === "true") {                
                $.ajax({
                    type: 'GET',
                    url: '/container_challenges/info?challenge_id=' + challenge_id + '&user_id=' + user_id,
                    headers: headers,
                    dataType: 'json',
                    data: JSON.stringify(body),
                    success: function (result) {
                        $("#deployment").html('<div><button onclick="stop_challenge(' + challenge_id + ',' + user_id + ',' + '\'' + nonce + '\'' +')" class="btn btn-outline-secondary"><i class="fas fa-stop"></i> Stop Challenge</button><div><div class="table-responsive" id="deployinfo"></div>');
                        show_info(result);
                        return;
                    },
                    error: function (result) {
                        $('#deployment').html('<div class="text-center">Cannot extract information from challenge container!</div>');
                        return;
                    }
                });
            }
            if (found === "false") {
                $("#deployment").html('<div><button onclick="start_challenge(' + challenge_id + ',' + user_id + ',' + '\'' + nonce + '\'' +')" class="btn btn-outline-secondary"><i class="fas fa-play"></i> Start Challenge</button><div><div class="table-responsive" id="deployinfo"></div>');
            }
        },
        error: function (result) {
            $('#deployment').html('<div class="text-center">Cannot retrieve challenge status!</div>');
        }
    });
}

function start_challenge(challenge_id, user_id, nonce) {

    $('#deployment').html('<div class="text-center"><i class="fas fa-circle-notch fa-spin fa-1x"></i></div>');

    headers = { "CSRF-Token": nonce, 'Content-Type': 'application/json' };
    body = { "challenge_id": challenge_id, "user_id": user_id };

    $.ajax({
        type: 'POST',
        url: '/container_challenges/namespace',
        headers: headers,
        dataType: 'json',
        data: JSON.stringify(body),
        success: function (result) {
            $.ajax({
                type: 'POST',
                url: '/container_challenges/rbac',
                headers: headers,
                dataType: 'json',
                data: JSON.stringify(body),
                success: function (result) {
                    body["role_name"] = result["role_name"];
                    $.ajax({
                        type: 'POST',
                        url: '/container_challenges/job',
                        headers: headers,
                        dataType: 'json',
                        data: JSON.stringify(body),
                        success: function (result) {
                            $.ajax({
                                type: 'GET',
                                url: '/container_challenges/info?challenge_id=' + challenge_id + '&user_id=' + user_id,
                                headers: headers,
                                dataType: 'json',
                                data: JSON.stringify(body),
                                success: function (result) {
                                    $("#deployment").html('<div><button onclick="stop_challenge(' + challenge_id + ',' + user_id + ',' + '\'' + nonce + '\'' +')" class="btn btn-outline-secondary"><i class="fas fa-stop"></i> Stop Challenge</button><div><div class="table-responsive" id="deployinfo"></div>');
                                    show_info(result);
                                    return;
                                },
                                error: function (result) {
                                    $('#deployment').html('<div class="text-center">Cannot extract information from challenge container!</div>');
                                    return;
                                }
                            });
                        },
                        error: function (result) {
                            $('#deployment').html('<div class="text-center">Cannot deploy job in challenge container namespace!</div>');
                            return;
                        },
                    });
                },
                error: function (result) {
                    $('#deployment').html('<div class="text-center">Cannot deploy RBAC in challenge container namespace!</div>');
                    return;
                },
            });
        },
        error: function (result) {
            $('#deployment').html('<div class="text-center">Cannot deploy challenge container namespace!</div>');
            return;
        }
    });
};

function stop_challenge(challenge_id, user_id, nonce) {

    if (typeof challenge_id === "number") {
        challenge_id = String(challenge_id);
    }
    if (typeof user_id === "number") {
        user_id = String(user_id);
    }

    headers = { "CSRF-Token": nonce, 'Content-Type': 'application/json' };
    body = { "challenge_id": challenge_id, "user_id": user_id };

    $.ajax({
        type: 'DELETE',
        url: '/container_challenges/namespace',
        headers: headers,
        dataType: 'json',
        data: JSON.stringify(body),
        success: function (result) { $('#deployment').html('<div class="text-center">Challenge container undeployed!</div>'); },
        error: function (result) { $('#deployment').html('<div class="text-center">Cannot undeploy challenge container!</div>'); }
    });
};

function show_info(data) {

    for (let k in data) {
        if (k === "hyperlinks") {
            var thead = document.createElement('thead');
            thead.classList.add("thead-light");
            var tbody = document.createElement('tbody');

            
            var name = document.createElement('th');
            var nametext = document.createTextNode("Name");
            name.setAttribute("data-field", "name");
            name.appendChild(nametext);

            var url = document.createElement('th');
            var urltext = document.createTextNode("URL");
            url.setAttribute("data-field", "url");
            url.appendChild(urltext);
            
            var tr = document.createElement('tr');
            tr.appendChild(name);
            tr.appendChild(url);
            thead.appendChild(tr);

            for (const service of data[k]) {
                var name = document.createElement('td');
                var nametext = document.createTextNode(service["name"]);
                name.appendChild(nametext);

                var url = document.createElement('td');
                var urltext = document.createTextNode(service["url"]);
                url.appendChild(urltext);
                
                var tr = document.createElement('tr');
                tr.appendChild(name);
                tr.appendChild(url);
                tbody.appendChild(tr);
            }
            
            var hyperlinks = document.createElement('table');
            hyperlinks.classList.add("table");
            hyperlinks.id = "hyperlinkstable";
            hyperlinks.appendChild(thead);
            hyperlinks.appendChild(tbody);

            document.getElementById('deployinfo').appendChild(hyperlinks);
        }

        if (k === "nodes") {
            var div = document.getElementById('deployinfo');
            var nodes = document.createElement('table');
            nodes.classList.add("table");
            nodes.id = "nodestable";

            var thead = document.createElement('thead');
            thead.classList.add("thead-light");

            var tbody = document.createElement('tbody');

            var tr = document.createElement('tr');
            var name = document.createElement('th');
            var nametext = document.createTextNode("Name");
            name.setAttribute("data-field", "name");
            name.appendChild(nametext);

            var addresses = document.createElement('th');
            var addresstext = document.createTextNode("Addresses");
            addresses.setAttribute("data-field", "addresses");
            addresses.appendChild(addresstext);

            tr.appendChild(name);
            tr.appendChild(addresses);
            thead.appendChild(tr);
            nodes.appendChild(thead);

            for (const node of data[k]) {
                var tr = document.createElement('tr');

                var name = document.createElement('td');
                var nametext = document.createTextNode(node["name"]);
                name.appendChild(nametext);

                var addresses = document.createElement('td');
                var addresstext = document.createTextNode(JSON.stringify(node["addresses"]));
                addresses.appendChild(addresstext);

                tr.appendChild(name);
                tr.appendChild(addresses);
                tbody.appendChild(tr);
            }

            nodes.appendChild(tbody);
            div.appendChild(nodes);
        }

        if (k === "services") {
            var div = document.getElementById('deployinfo');
            var services = document.createElement('table');
            services.classList.add("table");
            services.id = "servicestable";

            var thead = document.createElement('thead');
            thead.classList.add("thead-light");

            var tbody = document.createElement('tbody');

            var tr = document.createElement('tr');
            var name = document.createElement('th');
            var nametext = document.createTextNode("Name");
            name.setAttribute("data-field", "name");
            name.appendChild(nametext);

            var targetPort = document.createElement('th');
            var targetPortText = document.createTextNode("targetPort");
            targetPort.setAttribute("data-field", "ports");
            targetPort.appendChild(targetPortText);

            var nodePort = document.createElement('th');
            var nodePortText = document.createTextNode("nodePort");
            nodePort.setAttribute("data-field", "ports");
            nodePort.appendChild(nodePortText);

            var clusterip = document.createElement('th');
            var iptext = document.createTextNode("ClusterIP");
            clusterip.setAttribute("data-field", "clusterIP");
            clusterip.appendChild(iptext);

            tr.appendChild(name);
            tr.appendChild(clusterip);
            tr.appendChild(targetPort);
            tr.appendChild(nodePort);
            thead.appendChild(tr);
            services.appendChild(thead);

            for (const service of data[k]) {
                var tr = document.createElement('tr');

                var name = document.createElement('td');
                var nametext = document.createTextNode(service["name"]);
                name.appendChild(nametext);

                var targetPortInfo = document.createElement('td');
                var targetPortInfoText = document.createTextNode(JSON.stringify(service["ports"][0]["targetPort"]));
                targetPortInfo.appendChild(targetPortInfoText);

                var nodePortInfo = document.createElement('td');
                var nodePortInfoText = document.createTextNode(JSON.stringify(service["ports"][0]["nodePort"]));
                nodePortInfo.appendChild(nodePortInfoText);

                var clusterip = document.createElement('td');
                var iptext = document.createTextNode(service["clusterIP"]);
                clusterip.appendChild(iptext);

                tr.appendChild(name);
                tr.appendChild(clusterip);
                tr.appendChild(targetPortInfo);
                tr.appendChild(nodePortInfo);
                tbody.appendChild(tr);
            }

            services.appendChild(tbody);
            div.appendChild(services);
        }
    }

    return;
};