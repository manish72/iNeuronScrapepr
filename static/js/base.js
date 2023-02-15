/* function for getting the values of second dropdown */
function getCategories(data) {
    let val1 = document.getElementById("test").value;
    let select1 = document.getElementById("test1");
    let sec_drop = document.getElementById("dropList2");

    if (select1.hasChildNodes()) {
        while (select1.hasChildNodes()) {
            select1.removeChild(select1.firstChild);
        }
    }

    for(let temp of Object.values(data[val1])){
        var optionElement = document.createElement("option");
        optionElement.value = temp.title;
        optionElement.id = temp.id;
        optionElement.text = temp.title;
        select1.appendChild(optionElement);
    }

    sec_drop.style.display = "block";
    
}

/*Get list of Courses from sub-category*/
function redirectURL(){
    let sec_dropdown = document.getElementById("test1");
    opID = "";
    if (sec_dropdown.hasChildNodes()){
        for(let i=0; i < sec_dropdown.childNodes.length;i++){
            if(sec_dropdown.childNodes[i].value == sec_dropdown.value){
                opID = sec_dropdown.childNodes[i].id
            }
        }
        document.getElementById("submitID").href = '/subcategory?id='+opID;
    }
}