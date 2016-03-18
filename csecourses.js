// How many levels of classes we're considering
var LEVELS = 3;
var NODE_RADIUS = 20;

// Whether nodes are fixed or not
// Display style
var DisplayEnum = Object.freeze({FIXED: 0, MOTILE: 1, FIXEDMOTILE: 2});
var display = DisplayEnum.FIXED;

// Bounds for the graph
var w,h;
switch (display) {
	case DisplayEnum.MOTILE:
		if (LEVELS < 4) {
			w = 1200;
			h = 700;
			break;
		}
		// Fall through if levels >= 4
	case DisplayEnum.FIXED:
	case DisplayEnum.FIXEDMOTILE:
		w = 2400;
		h = 480;
		break;
}

// All the variables for D3
var svg;
var link, node, text, linkText;

if (display == DisplayEnum.MOTILE) {
	var bounds;
}

// DATA VARIABLES
var nodes, links;

var force;

// Input files
var filenames = ["csecourses/testcourses"+ LEVELS + "-alt.json", "csecourses/testlinks"+ LEVELS + "-alt.json"];

// Kickstart the process by first loading the files
loadFiles(filenames);

/**
 * Loads the given list of file names. Calls onFilesLoaded when files are 
 * done loading.
 */
function loadFiles(filenames) {
	var q = queue();

	filenames.forEach(function(d) {
		q.defer(d3.json, d);
	});
	q.awaitAll(main);
}

/**
 * MAIN ENTRY POINT FOR CODE
 */
function main(err, results) {
	if (err) {
		console.log(err);
		return;
	}
	setup(results);
	drawEverything();

	if(display == DisplayEnum.FIXED || display == DisplayEnum.FIXEDMOTILE) {
		fixedForceGraph(force);
	}
}

/**
 * Sets everything up.
 */
function setup(results) {
	nodes = results[0];
	links = results[1];

	if (display == DisplayEnum.FIXED) {
		setupFixedNodes(d3.values(nodes));
	}

	if (display == DisplayEnum.FIXEDMOTILE) {
		setupFixedMotileNodes(nodes);
	}

	// Attaching node objects (from node indices) to links
	links.forEach(function(link) {
		link.source = nodes[link.source];
		link.target = nodes[link.target];
	});

	// Main part of force layout
	force = d3.layout.force()
		.size([w, h])
		.nodes(d3.values(nodes))  // the nodes parameter needs to be an array, not a map
		.links(links);

	if (display == DisplayEnum.MOTILE) {
		// Allows for movement of the nodes
		force.charge(-500)
			.on("tick", tick)
			.start();
	}

	// Access to the SVG container
	svg = d3.select("body").append("svg")
		.attr("width", w)
		.attr("height", h);
}

/**
 * Adds all the SVG elements to the container, using the force object.
 */
function drawEverything() {
	// Links
	link = svg.append("g").selectAll(".link")
		.data(force.links()).enter()
		// This is of type <path>, because it might potentially be a curve,
		// not just a straight <line>.
		.append("path")
		// Changes the color of the link if there's a minimum GPA requirement
		.attr("class", function(d) {
			return "link" + (d.hasOwnProperty('gpa') ? " gpa" : "");
		})
		// Attaches marker (arrow) to the end of the link
		// As of now the regular link is just called "regular"
		.style("marker-end", function(d) {
			return "url(#" + (d.hasOwnProperty('gpa') ? "gpa" : "regular") + ")";
		});

	// Link end arrows
	svg.append("defs").selectAll("marker")
			.data(["regular","gpa"]).enter()
		.append("marker")
			.attr("id", function(d) { return d; })
			.attr("viewBox", "0 -5 10 10")			// Viewport for the arrow
			.attr("refX", 27).attr("refY", 0)		// Offset from the center of the node
			.attr("markerWidth", 6).attr("markerHeight", 6)
													// Bounding-box attributes
			.attr("orient", "auto")
		.append("path")
			// Draws the triangle, pointing right. M denotes start, L is each point
			.attr("d", "M0,-5L10,0L0,5");

	var tip = d3.tip()
      .attr('class', 'd3-tip')
      .offset([-10, 0])
      .html(function(d) {
         x = "<strong>Name:</strong> <span class='tooltip-info'>" + d["name"] + "</span>";
         return x;
  });

	// Nodes
	node = svg.append("g").selectAll(".node")
		.data(force.nodes()).enter()
		.append("circle")
		.attr('r', NODE_RADIUS)
		.attr("class", function(d) {
			return "node" + (d.hasOwnProperty("classification") ? (" " + d["classification"]) : "");
		});

	if (display == DisplayEnum.MOTILE) {
		node.call(force.drag);
	}

	node.call(tip);

  node.on("mouseover", function(d) {
    tip.show(d);
    /*var descendantResults = new Set();
    getTraversal(d, descendantResults, parentToChildDirectory);
    var ancestorResults = new Set();
    getTraversal(d, ancestorResults, childToParentDirectory);
    
    set_focus(d, circle, text, path, ancestorResults, descendantResults)
    set_highlight(d, circle, text, path, ancestorResults, descendantResults);*/
  });

  node.on("mouseout", function(d) {
    /*if (!clicked) {
          focus_node = null;
          if (highlight_trans<1)
          {
      
        circle.style("opacity", 1);
        text.style("opacity", 1);
      }
      exit_highlight(circle, text, path);
    }*/
    tip.hide(d);
  });

	// Text
	text = svg.append("g").selectAll(".text")
		.data(force.nodes()).enter()
		.append("text")
		.text(function(d) { return d.number; });

	if (display == DisplayEnum.MOTILE) {
		text.attr("x", 25)
			.attr("y", ".31em");
	}

	// Extract out links with GPA values
	gpaLinks = getGpaLinks(links);
	
	// Link GPA Text
	linkText = svg.append("g").selectAll(".linkText")
		.data(gpaLinks).enter()
		.append("text")
		.attr("dy", ".35em")
		.attr("fill", "Black")
		.text(function(d) {
			// Make sure there's 1 decimal place
			return Number(d.gpa).toFixed(1);
		});

	if (display == DisplayEnum.MOTILE) {
		// 1, 3
		bounds = [
			{x: 200, y: 100, width: 400, height: 400},
			{x: 700, y: 100, width: 400, height: 400}
		];

		// Rectangles for 100 and 300 level courses
		var rectangle = svg.append("g").selectAll(".bounds")
			.data(bounds).enter()
			.append("rect")
			.attr({
				x: function(d) { return d.x-5; },
	        	y: function(d) { return d.y-5; },
	        	width: function(d) { return d.width+10; },
	        	height: function(d) { return d.height+10; }
			}).style({
				fill: "white",
				stroke: "black",
				"stroke-width": 5
			});
	}
}

/**
 * Attaching data to elements: fixed force graph
 */
function fixedForceGraph(force) {	
	force.on('end', function() {
		node.attr('cx', function(d) { return d.x; })
			.attr('cy', function(d) { return d.y; });
	
		/*link.attr('x1', function(d) { return d.source.x; })
			.attr('y1', function(d) { return d.source.y; })
			.attr('x2', function(d) { return d.target.x; })
			.attr('y2', function(d) { return d.target.y; });*/
		link.attr("d", linkLine);

		text.attr("x", function(d) { return d.x - 12; })
			.attr("y", function(d) { return d.y + NODE_RADIUS*2- 5; });

		linkText.attr("x", function(d) { return linkTextPos(d, "x"); });
		linkText.attr("y", function(d) { return linkTextPos(d, "y"); });

		console.log("Done!");
		d3.select("body").append("p").text("Done Loading!");
	});

	force.start();
}

/** 
 * Attaching data to elements: moving force graph
 */
function tick() {
	link.attr("d", linkLine);

	// Bounding in a particular box
	node.attr("cx", function(d) {
			if (courseLevel(d.number) == 3) {
				return d.x = Math.max(bounds[1].x + NODE_RADIUS, Math.min(bounds[1].x + bounds[1].width - NODE_RADIUS, d.x));
			} else {
				return d.x = Math.max(bounds[0].x + NODE_RADIUS, Math.min(bounds[0].x + bounds[0].width - NODE_RADIUS, d.x));
			}
		}).attr("cy", function(d) {
			if (courseLevel(d.number) == 3) {
				return d.y = Math.max(bounds[1].y + NODE_RADIUS, Math.min(bounds[1].y + bounds[1].height - NODE_RADIUS, d.y));
			} else {
				return d.y = Math.max(bounds[0].y + NODE_RADIUS, Math.min(bounds[0].y + bounds[0].height - NODE_RADIUS, d.y));
			}
		});

	//node.attr("transform", transform);

	text.attr("transform", transform);
	
	// The parameter for attr is a function, whose parameter is each individual element
	linkText.attr("x", function(d) { return linkTextPos(d, "x"); });
	linkText.attr("y", function(d) { return linkTextPos(d, "y"); });
}

// Helper for tick() to create appropriate text for transform
function transform(d) {
	return "translate(" + d.x + "," + d.y + ")";
}

//////////////// DRAWING HELPER METHODS ////////////////
// Sets the position of the link text.
function linkTextPos(d, coord) {
	if (d.target[coord] > d.source[coord]) {
		return (d.source[coord] + (d.target[coord] - d.source[coord])/2);
	} else {
		return (d.target[coord] + (d.source[coord] - d.target[coord])/2);
	}
}

// Draws an arc from the source to the target.
function linkArc(d) {
	var dx = d.target.x - d.source.x;
	var dy = d.target.y - d.source.y;
	var dr = Math.sqrt(dx * dx + dy * dy);
	return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
}

// Draws a line from the source to the target
function linkLine(d) {
	return "M" + d.source.x + "," + d.source.y + "L" + d.target.x + "," + d.target.y;
}

///////////// HELPER METHODS /////////////

/**
 * Sets up nodes for fixed-motile mode
 *
 * @param nodes an object representing the nodes
 */
function setupFixedMotileNodes(nodes) {
	var levelledNodes = getLevelledNodes(nodes);

	levelledNodes.forEach(function(aLevelOfNodes, i) {
	//var aLevelOfNodes = levelledNodes[0];
		var x = 100+(i*350), y = 100;  // rectangle upper left corner
		var nodecount = aLevelOfNodes.length;
		var nodediameter = 2*NODE_RADIUS;
		var sp = 25;
		var c = 5;  // columns

		var w = (nodediameter+sp)*c + sp;
		var r = Math.ceil(nodecount / c);

		var n;
		for (var i = 0; i < r; i++) {
			for (var j = 0; j < c; j++) {
				if ((i*c + j) >= nodecount) break; // should already be on the last row
				n = aLevelOfNodes[i*c + j];

				n.x = x + ((j+1) * sp) + ((j + 0.5) * nodediameter);
				n.y = y + ((i+1) * sp) + ((i + 0.5) * nodediameter);

				n.fixed = true; 
			}
		}
	});

	//console.log(nodes);
}

/**
 * Breaks up the nodes object into an array of arrays by level.
 * TODO: replace with .nest()?
 */
function getLevelledNodes(nodes) {
	var levelledNodes = [];  // 2D array of levels
	var currentLevelNodes = [];
	var currentLevel = 1;

	var courseCodes = d3.keys(nodes).sort();

	courseCodes.forEach(function(code) {
		// Place each node appropriately in the levelledNodes 2D array
		var level = courseLevel(parseInt(code));
		if (level != currentLevel) {
			levelledNodes.push(currentLevelNodes);
			currentLevelNodes = [];
			currentLevel = level;
		}
		currentLevelNodes.push(nodes[code]);
	});

	levelledNodes.push(currentLevelNodes);  // fencepost

	return levelledNodes;
}

/**
 * If the force graph is fixed, sets nodes' positions.
 *
 * @param nodes the array of nodes
 */
function setupFixedNodes(nodes) {
	// Sets the positions of the given nodes
	var BASE_X = 60;
	var LEVEL_OFFSET = 150;
	var NODE_OFFSET = 30;
	
	var currentLevel = 1;
	var xCounter = 0;
	var yShift = false;

	nodes.forEach(function(n) {
		var level = Math.floor(n.number / 100);
		level = (level != 1 ? level - 2 : level - 1);
		
		// Updates level
		if (level != currentLevel) {
			currentLevel = level;
			xCounter = 0;
		}

		n.x = BASE_X + (xCounter * (NODE_RADIUS + NODE_OFFSET));
		n.y = (LEVEL_OFFSET / 2) + (level * LEVEL_OFFSET) + (yShift ? 30 : 0);
		// Doesn't allow force to actually modify the positions of the nodes
		n.fixed = true;
		
		xCounter++;
		yShift = !yShift;
	});
}

/**
 * Only gets the links that have GPAs.
 */
function getGpaLinks(links) {
	gpaLinks = [];

	links.forEach(function(link) {
		if(link.hasOwnProperty('gpa')) {
			gpaLinks.push(link);
		}
	});

	return gpaLinks;
}

/**
 * Returns true if the given number is at the given level.
 */
function courseLevel(number) {
	return (Math.floor(number / 100));
}