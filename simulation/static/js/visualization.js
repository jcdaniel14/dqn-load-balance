
    let data =JSON.parse($("#results").val());

    result =data.interfaces.map((obj, i) => {
    return {
      id:obj.interface_id,
      name: obj.interface,
      local: obj.local
    };
  });

    steps = data.steps;
    width = 800;
    hueRange = 0.45;
    lightnessRange = 0.15;
    hueStart = 0.7;
    lightnessStart = 0.85;
    chroma = 0.2;
    selectedStep =1;
    textWidth = 640;
    seed =1;

    colorGris= "rgb(241, 246, 250)";
    colorNaranja= "rgb(253, 242, 233)";
    colorCeleste= "rgb(235, 245, 251)";
    colorAmarillo= "rgb(252, 243, 207)";
    colorVerde= "rgb(212, 239, 223 )";
    backgroundSquare = "rgb(21, 67, 96)";

    let div = d3.select("#step_results").style("max-width", `${textWidth}px`).style("font-family", "sans-serif");


    let colorCiudad = d3
      .scaleOrdinal()
      .domain(["uio", "gye"])
      .range([colorNaranja, colorCeleste]);

  const controls = div.append("div")
    .style("display", "flex")
    .style("align-items", "center")
    .style("gap", "4px");



  // replay button
  controls.append("button")
    .attr("class","btn btn-primary")
    .text("Replay")
    .on("click", d => {
      replay();
      //div.node().dispatchEvent(new CustomEvent("input"));
    });

  // navigate step
  controls.append("input")
    .attr("type","range")
    .attr("min","1")
    .attr("max",steps.length)
    .on("input",  function() {

       item = steps[this.value-1];
       console.log(this.value, item);
        graph.updateLinks(item.source-1,item.target-1);
        title.text("Paso " + (this.value));
    });
    const title = controls.append("p").attr("class","title_step mt-3");


let graph = chart();

const sleepNow = (delay)=>new Promise((resolve)=> setTimeout(resolve,delay));

async function replay(){
    let item = steps[0];
    title.text("Paso 1 ");
     graph.updateLinks(item.source-1,item.target-1);
    for(let i=1;i<steps.length; i++){
        await sleepNow(1500);
        item = steps[i];
        graph.updateLinks(item.source-1,item.target-1);
        console.log(item);
        title.text("Paso " + (i+1));
    }
}
 replay();
function chart() {
  const padding = 6;
  const margin = 3;
  const strokeWidth = 1;
  const gap = 1;
  const nameHeight = 14;
  const stageWidth = Math.min(textWidth, width);
  const middleWidth = Math.max(80, stageWidth - 2 * textWidth / 3 - 2 * nameHeight);
  const nameWidth = (stageWidth - middleWidth) / 2;
  const sectionHeight = nameHeight + gap + 2 * padding;

  // Must initialize with a dummy dataViz to make the updates work
  const dataViz = result.map((obj, i) => {
    const l = lightnessStart - ((result.length - 1 - i) / result.length) * lightnessRange;
    const h = i / result.length * 360 * hueRange + hueStart * 360
    return {
      obj,
      position: i,
      id:obj.id,
      name: obj.name,
      color: colorCiudad(obj.local)
    };
  });



  // define height of div based on length of team list
  const height = sectionHeight * dataViz.length - gap;

  // Names lists
  const namesDiv = div.append("div")
    .style("position", "relative")
    .style("padding-bottom", "8px")

  // *First list*
  // creating divs for each name
  const firstList = namesDiv.append("div")
    .style("width", `${nameWidth}px`)
    .style("display", "grid")
    .style("grid-gap", gap + "px")

  // creating name div
  const alphaName = firstList.selectAll(".name")
      .data(dataViz, d => d.name)
    .join("div")
      .attr("class", "name")
      .style("display", "flex")
      .style("background",d=>d.color)
      .style("height", `${nameHeight + 2 * padding}px`)
      .style("overflow", "hidden")
      .style("font-size", `${nameHeight}px`)
      .style("font-weight", 500)
      .style("line-height", `${nameHeight}px`)
      .style("border-radius", "4px")

  // adding name
  alphaName.append("div")
    .style("padding", `${padding}px`)
    .style("flex-grow", 1)
    .text((d, i) => d.name);

  // adding square  - index
   alphaName.append("div")
    .attr("class", "swatch")
    .style("border-radius", "3px")
    .style("margin", margin + "px")
    .style("width", nameHeight + 2 * padding - 2 * margin + "px")
    .style("font-size", nameHeight - 2 + "px")
    .style("line-height", nameHeight + 2 * padding - 2 * margin + "px")
    .style("color", "white")
    .style("text-align", "center")
    .style("background", backgroundSquare)
    .text(d => d.id)

  // *Second list*
  // creating divs for each name
  const secondListDiv = namesDiv.append("div")
    .style("width", `${nameWidth}px`)
    .style("position", "absolute")
    .style("top", 0)
    .style("right", 0)

  // define transition
  const t = secondListDiv.transition().duration(1000);

  // creating the second list divs
  const secondList = secondListDiv.selectAll(".name")
    .data(dataViz, d => d.name)
    .join(
      enter => enter.append("div")
        .attr("class", "name")
        .style("position", "absolute")
        .style("display", "flex")
        .style("width", "100%")
        .style("background", (d)=> d.color)
        .style("height", `${nameHeight + 2 * padding}px`)
        .style("overflow", "hidden")
        .style("font-size", `${nameHeight}px`)
        .style("font-weight", 500)
        .style("line-height", `${nameHeight}px`)
        .style("border-radius", "4px")
        .style("left", "0px")
        .style("top", (d, i) => i * sectionHeight + "px")
    );

  // creating second list - squares
  const secondListSwatch = secondList.append("div")
    .attr("class", "swatch")
    .style("border-radius", "3px")
    .style("margin", margin + "px")
    .style("width", nameHeight + 2 * padding - 2 * margin + "px")
    .style("font-size", nameHeight - 2 + "px")
    .style("line-height", nameHeight + 2 * padding - 2 * margin + "px")
    .style("color", "white")
    .style("text-align", "center")
    .style("background",backgroundSquare)
  .text((d, i) => i + 1);


  // adding ordered list names
  secondList.append("div")
    .style("padding", `${padding}px`)
    .text((d, i) => d.name);

   // *SVG Connections (dashed lines)*
  // create svgs and groups for connections
  const connection = namesDiv.append("svg")
    .attr("width", middleWidth)
    .attr("height", height)
    .style("position", "absolute")
    .style("top", 0)
    .style("left", `${nameWidth}px`)
    .style("pointer-events", "none")
    .attr("fill", "none")
    .attr("stroke-width", strokeWidth)
    .attr("stroke", "rgb(78,121,167)")
    .attr("class","link")
    .attr("transform", `translate(0, ${sectionHeight / 2})`);

  // link generator
  const link = d3.linkHorizontal()

  // creates white space where the lines overlap one another
  let whitePath = connection.append("path")
    .attr("stroke", "white")
    .attr("stroke-width", strokeWidth + 2 * 2)
    .attr("class","linkWhitePath");

  // create path
  let coloredPath = connection.append("path")
    .style("stroke-dashArray", "8, 2")
    .attr("class","linkColoredPath");

  // create arrows
  let arrowHead = connection.append("path")
    .attr("d", `M${middleWidth - 4},0 m-4,-4 l4,4 l-4,4`)
    .attr("transform",`translate(0,-10)`)
    .attr("class","linkArrowHead");

  function updateLinks(source,target){
    const duration = 1500;
    // link generator
    const link = d3.linkHorizontal();
    let arrowHead = d3.select(".linkArrowHead");
    let coloredPath = d3.select(".linkColoredPath");
    let whitePath = d3.select(".linkWhitePath");

      arrowHead
         .transition()
         .attr(
          "transform",
          () => `translate(0, ${target* sectionHeight})`
        );

      coloredPath
        .transition()
        .attr("d", ()=> {
          const x2 = 0;
          const y2 = source * sectionHeight;
          const x1 = middleWidth - 4;
          const y1 = target * sectionHeight;
          return link({ source: [x1, y1], target: [x2, y2] });
        });

      whitePath
        .transition()
        .duration(duration)
        .attr("d", () => {
          const x2 = 0;
          const y2 = source * sectionHeight;
          const x1 = middleWidth - 4;
          const y1 = target * sectionHeight;
          return link({ source: [x1, y1], target: [x2, y2] });
        });
  }

  return Object.assign(div.node(), {updateLinks });
}

