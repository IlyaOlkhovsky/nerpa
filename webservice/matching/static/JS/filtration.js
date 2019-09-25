function Groups(name, type, title) {
    this.name = name;
    this.type = type;
    this.title = title;
}

var groups = [new Groups("All results", "none", "All results")];

function group_by_update() {
    var selector = document.getElementById('select_group_by');
    var choose_option = selector.options[selector.selectedIndex].value;
    $.ajax({
        type: "GET",
        url: this.href,
        data: {"request_type": "group_by", "value": choose_option},
        success: function (data) {
            document.getElementById('result_container').innerHTML = data;
        }
    });
}

function update_navigation() {
    var groupby_ul = document.getElementById('groupby_list');
    groupby_ul.innerHTML = "";
    for (var elem in groups) {
        groupby_ul.innerHTML += "<li class=\"inline_item\" onclick='change_group(" + elem + ")'> <a><span>" + groups[elem].title + "</span></a></li>\n"
    }
}


function generate_data_query() {
    var data_query = {};
    for (var elem in groups) {
        if (elem.type != "none") {
            data_query[elem.type] = elem.name;
        }
    }

    var min_len = document.getElementById("min_len").value;
    var min_score = document.getElementById("min_score").value;

    data_query["min_len"] = min_len;
    data_query["min_score"] = min_score;

    return data_query;
}

function generate_query() {
    var data_query = generate_data_query();

    $.ajax({
        type: "GET",
        url: this.href,
        data: data_query,
        success: function (data) {
            document.getElementById('result_container').innerHTML = data;
        }
    });
}

function change_group(eid) {
    groups = groups.slice(0, eid + 1);
    update_navigation();
    generate_query();
}


function choose_group(genome_id) {
    groups.push(new Groups(genome_id, "genome_id", "Genome id: " + genome_id));
    document.getElementById('select_group_by').value = "none";

    update_navigation();
    generate_query();
}