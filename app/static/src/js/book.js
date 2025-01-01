let currentLocation = '';
let rendition = '';
let isSidebarVisible = false; // Start with the sidebar visible
let lastAction = null; // Variable to keep track of the last clicked action

let book_width_max = '90vw';
let book_width_min = '75vw';
let book_height = 600;

function toggleSidebar(action, element) {
    const sidebar = document.getElementById('sidebar');
    const sidebarContent = document.getElementById(action);

    // Check if the same action button is clicked twice
    if (lastAction === action) {
        // If the same button is clicked, toggle the sidebar visibility
        isSidebarVisible = !isSidebarVisible;
        element.classList.remove("active");
    }
    else {
        // If a different button is clicked, show the sidebar and update content
        document.querySelectorAll('.action').forEach(item => {
            item.classList.remove("active");
        });
        isSidebarVisible = true;
        if (lastAction) {
            document.getElementById(lastAction).style.display = "none";
        }
        lastAction = action; // Update the last action clicked
        element.classList.add("active");
    }

    // Update the sidebar display based on the visibility state
    sidebar.style.display = isSidebarVisible ? 'block' : 'none';

    sidebarContent.style.display = isSidebarVisible ? 'block' : 'none';

    rendition.resize(width = isSidebarVisible ? book_width_min : book_width_max, height = book_height);

}

async function get_blob(book_id) {
    var finalURL = `/books/${book_id}`;
    var response = await fetch(finalURL);
    const data = await response.blob();
    return data;
}

async function get_location(id) {
    const url = "/position";
    var response = await fetch(url + "?" + new URLSearchParams({ book_id: id }).toString());
    const data = await response.json();
    return data.position;
}

async function set_location(position, id) {
    const url = "/position";
    url.search = new URLSearchParams({ book_id: id }).toString();
    var response = await fetch(url + "?" + new URLSearchParams({ book_id: id }).toString(), {
        method: 'POST',  // Use POST to match Flask route
        headers: {
            'Content-Type': 'application/json',  // Ensure correct content type for JSON
        },
        body: JSON.stringify({
            position: position
        })
    });
    const data = await response.json();
    return data.message;
}

async function parseCSS(cssText) {
    const rules = {};

    // Regular expression to match class-based styles, e.g., ".light { background: #fff; color: #000; }"
    const classRuleRegex = /\.([a-zA-Z0-9_-]+)\s*\{([^}]+)\}/g;

    let match;
    while ((match = classRuleRegex.exec(cssText)) !== null) {
        const className = match[1];
        const propertiesText = match[2];

        // Parse the CSS properties (e.g., "background: #fff; color: #000")
        const properties = {};
        const propertyRegex = /([a-zA-Z-]+)\s*:\s*([^;]+)\s*;/g;
        let propertyMatch;

        while ((propertyMatch = propertyRegex.exec(propertiesText)) !== null) {
            properties[propertyMatch[1]] = propertyMatch[2];
        }

        rules[className] = properties;
    }

    return rules;
}

function fetchCSS(url) {
    return fetch(url)
        .then(response => response.text())
        .then(cssText => parseCSS(cssText))
        .catch(error => console.error('Error fetching CSS:', error));
}

(async () => {

    var book_id = document.getElementById("bookfile").className;

    var blob_data = await get_blob(book_id);

    var book = ePub(blob_data);


    rendition = book.renderTo("viewer", {
        width: book_width_max,
        height: book_height,
        allowscriptedcontent: true,
    });

    currentLocation = await get_location(book_id);

    rendition.display(currentLocation);

    book.ready.then(() => {
        var next = document.getElementById("next");

        next.addEventListener("click", function (e) {
            book.package.metadata.direction === "rtl" ? rendition.prev() : rendition.next();
            e.preventDefault();
        }, false);

        var prev = document.getElementById("prev");
        prev.addEventListener("click", function (e) {
            book.package.metadata.direction === "rtl" ? rendition.next() : rendition.prev();
            e.preventDefault();
        }, false);

        var keyListener = function (e) {

            // Left Key
            if ((e.keyCode || e.which) == 37) {
                book.package.metadata.direction === "rtl" ? rendition.next() : rendition.prev();
            }

            // Right Key
            if ((e.keyCode || e.which) == 39) {
                book.package.metadata.direction === "rtl" ? rendition.prev() : rendition.next();
            }

        };

        rendition.on("keyup", keyListener);
        document.addEventListener("keyup", keyListener, false);

    });

    rendition.on("relocated", async function (location) {

        currentLocation = location.start.cfi;
        await set_location(currentLocation, book_id);

        var next = book.package.metadata.direction === "rtl" ? document.getElementById("prev") : document.getElementById("next");
        var prev = book.package.metadata.direction === "rtl" ? document.getElementById("next") : document.getElementById("prev");

        if (location.atEnd) {
            next.style.visibility = "hidden";
        }
        else {
            next.style.visibility = "visible";
        }

        if (location.atStart) {
            prev.style.visibility = "hidden";
        }
        else {
            prev.style.visibility = "visible";
        }

    });

    rendition.on("layout", function (layout) {
        let viewer = document.getElementById("viewer");

        if (layout.spread) {
            viewer.classList.remove('single');
        }
        else {
            viewer.classList.add('single');
        }
    });

    window.addEventListener("unload", function () {
        console.log("unloading");
        this.book.destroy();
    });

    book.loaded.navigation.then(function (toc) {
        var select = document.getElementById("toc");
        var docfrag = document.createDocumentFragment();

        toc.forEach(function (chapter) {
            var option = document.createElement("div");
            if (chapter.subitems.length > 0) {
                option.className = "toc-item";

                option.setAttribute("data-target", `toc-${chapter.label.replace(/\s+/g, '-').toLowerCase()}`);
                option.innerHTML = `<svg class="bi" width="1em" height="1em" fill="currentColor"><use xlink:href="/bootstrap/static/icons/bootstrap-icons.svg#chevron-right"></use></svg> <span>${chapter.label}</span>`;

                // Display chapter
                option.getElementsByTagName("span")[0].onclick = function () {
                    document.querySelectorAll('.toc-item').forEach(item => {
                        if (item !== option) {
                            item.classList.remove("active");
                        }
                    });
                    option.classList.toggle('active');
                    rendition.display(chapter.href);

                };

                docfrag.appendChild(option);

                var dropdonw = document.createElement("div");
                dropdonw.className = "toc-content";
                dropdonw.id = `toc-${chapter.label.replace(/\s+/g, '-').toLowerCase()}`;

                // For each sub section
                chapter.subitems.forEach(function (subitems) {
                    var sub = document.createElement("div");
                    sub.className = "toc-item";
                    sub.setAttribute("data-target", `toc-${subitems.label.replace(/\s+/g, '-').toLowerCase()}`);
                    sub.textContent = subitems.label;
                    sub.onclick = function () {
                        document.querySelectorAll('.toc-item').forEach(item => {
                            if (item !== sub) {
                                item.classList.remove("active");
                            }
                        });
                        sub.classList.toggle('active');
                        rendition.display(subitems.href);
                    };
                    dropdonw.appendChild(sub);
                });
                docfrag.appendChild(dropdonw);
            }

            else {
                option.className = "toc-item";
                option.setAttribute("data-target", `toc-${chapter.label.replace(/\s+/g, '-').toLowerCase()}`);
                option.textContent = chapter.label;
                option.onclick = function () {
                    document.querySelectorAll('.toc-item').forEach(item => {
                        if (item !== option) {
                            item.classList.remove("active");
                        }
                    });
                    rendition.display(chapter.href)
                    option.classList.toggle('active');
                };

                docfrag.appendChild(option);
            }

        });

        const tocContainer = document.getElementById("toc");
        tocContainer.addEventListener('click', function (e) {
            const target = e.target.closest('.toc-item');
            const target_svg = e.target.closest('svg');
            const contentId = target.getAttribute("data-target");
            const content = document.getElementById(contentId);

            if (target && target_svg && content) {
                // If the content exists, toggle its visibility
                content.classList.toggle('active');
                const svg = target.querySelector('svg');
                if (svg) {
                    svg.innerHTML = content.classList.contains('active')
                        ? '<use xlink:href="/bootstrap/static/icons/bootstrap-icons.svg#chevron-down"></use>'
                        : '<use xlink:href="/bootstrap/static/icons/bootstrap-icons.svg#chevron-right"></use>';
                }
            }
        });

        select.appendChild(docfrag);

    });

    rendition.themes.register('light', "/static/dist/css/theme.css");
    rendition.themes.register('dark', "/static/dist/css/theme.css");
    rendition.themes.register('tan', "/static/dist/css/theme.css");

    const colorBoxes = document.querySelectorAll('.color-box');
    colorBoxes.forEach(colorBox => {
        colorBox.addEventListener('click', () => {
            // Remove active class from all boxes
            colorBoxes.forEach(box => box.classList.remove('active'));

            // Add active class to clicked box
            colorBox.classList.add('active');


            // Get selected color and apply to body background

            const selectedColor = colorBox.dataset.color;
            fetchCSS(rendition.themes._themes[selectedColor]["url"])
                .then(rules => {

                    const colorTheme = rules[selectedColor];

                    // Apply the styles dynamically
                    if (colorTheme) {
                        document.body.style.background = colorTheme.background;
                        document.body.style.color = colorTheme.color;
                    }
                });

            rendition.themes.select(colorBox.getAttribute("data-color"));
        });
    });

    var pageView = document.getElementById("pageView");
    pageView.onchange = function () {
        rendition.spread(pageView.value);
    };

    var fontFamily = document.getElementById("fontFamily");
    fontFamily.onchange = function () {
        if (fontFamily.value == "default") {
            rendition.themes.removeOverride("font-family");
        }
        else {
            rendition.themes.font(fontFamily.value);
        }
    };

    var fontsize = document.getElementById("fontsize");
    fontsize.onchange = function () {
        if (fontsize.value) {
            rendition.themes.fontSize(fontsize.value + "px");
        }
        else {
            rendition.themes.removeOverride("font-size");
        }

    }

    var default_size = 16;
    document.getElementById("stepdown").onclick = function () {
        if (fontsize.value && parseInt(fontsize.value) - 1 >= parseInt(fontsize.min)) {
            fontsize.value = parseInt(fontsize.value) - 1;
        }
        else {
            fontsize.value = default_size;
        }
        fontsize.dispatchEvent(new Event("change"));
    }

    document.getElementById("stepup").onclick = function () {
        if (fontsize.value && parseInt(fontsize.value) + 1 <= parseInt(fontsize.max)) {
            fontsize.value = parseInt(fontsize.value) + 1;
        }
        else {
            fontsize.value = default_size;
        }
        fontsize.dispatchEvent(new Event("change"));
    }

    document.getElementById("clear").onclick = function () {
        fontsize.value = null;
        fontsize.placeholder = "default";
        fontsize.dispatchEvent(new Event("change"));
    }

})();


window.onload = () => {
    var book_id = document.getElementById("bookfile").className;
    fetch(`/has_rated/${book_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            book_id: book_id
        })
    }).then(response => response.json())
        .then(data => {
            document.querySelectorAll('.form-rating input').forEach(radio => {
                if (parseFloat(radio.value) == data.rating) {
                    radio.checked = true;
                }
            });

        })

};

var book_id = document.getElementById("bookfile").className;
document.querySelectorAll('.form-rating input').forEach(radio => {
    radio.addEventListener('change', function () {
        var rating = radio.value;

        fetch(`/rating/${book_id}/${rating}`, {
            method: 'POST',  // Use POST to match Flask route
            headers: {
                'Content-Type': 'application/json',  // Ensure correct content type for JSON
            },
            body: JSON.stringify({
                book_id: book_id,
                rating: rating
            })
        }).then(response => response.json())  // Read the response as text
            .then(data => document.getElementById("avg-rating").innerText = `Average Rating: ${data.rating}`)

    });
});