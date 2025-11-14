# Interactive Relationship Graph

<link href="https://unpkg.com/vis-network/styles/vis-network.min.css" rel="stylesheet" type="text/css" />

<div id="network"></div>

<div id="controls" style="margin-top: 20px;">
  <h3>Controls</h3>
  <button onclick="fitNetwork()">Fit to Screen</button>
  <button onclick="filterNodes('all')">Show All</button>
  <button onclick="filterNodes('people')">People Only</button>
  <button onclick="filterNodes('organizations')">Organizations Only</button>
  <button onclick="filterNodes('locations')">Locations Only</button>
  <button onclick="filterNodes('events')">Events Only</button>
</div>

<div id="legend" style="margin-top: 20px;">
  <h3>Legend</h3>
  <ul>
    <li><span style="color: #3399ff; font-weight: bold;">🔵 Blue:</span> People</li>
    <li><span style="color: #33cc33; font-weight: bold;">🟢 Green:</span> Organizations</li>
    <li><span style="color: #ff6666; font-weight: bold;">🔴 Red:</span> Locations</li>
    <li><span style="color: #ffcc00; font-weight: bold;">🟡 Yellow:</span> Events/Dates</li>
  </ul>
</div>

<div id="info" style="margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px;">
  <p><strong>Graph Statistics:</strong></p>
  <ul>
    <li>Showing top 500 most-mentioned entities</li>
    <li>500,000 total relationships in database</li>
    <li>6,607 total entities across all types</li>
  </ul>
</div>

<script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

<script type="text/javascript">
  let network;
  let allData;
  let currentFilter = 'all';

  // Show loading message
  document.getElementById('network').innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 18px; color: #666;">Loading graph data...</div>';

  // Load graph data
  fetch('../assets/graph_viz.json')
    .then(response => response.json())
    .then(data => {
      allData = data;
      // Start with "People Only" filter to avoid initial chaos
      filterNodesOnLoad('people', data);
    })
    .catch(error => {
      console.error('Error loading graph data:', error);
      document.getElementById('network').innerHTML = '<p style="color: red;">Error loading graph data. Please ensure graph_viz.json is in the assets folder.</p>';
    });

  function initNetwork(data) {
    const container = document.getElementById('network');

    // Define color mapping for entity types
    const colorMap = {
      'people': '#3399ff',
      'organizations': '#33cc33',
      'locations': '#ff6666',
      'events': '#ffcc00'
    };

    // Process nodes with colors
    if (data.nodes) {
      data.nodes = data.nodes.map(node => {
        const type = node.group || node.type || 'people';
        return {
          ...node,
          color: colorMap[type] || '#999999',
          group: type
        };
      });
    }

    const options = {
      nodes: {
        shape: 'dot',
        size: 16,
        scaling: {
          min: 10,
          max: 40,
          label: {
            enabled: true,
            min: 12,
            max: 20
          }
        },
        font: {
          size: 14,
          face: 'Tahoma',
          color: '#000000',
          strokeWidth: 2,
          strokeColor: '#ffffff'
        },
        borderWidth: 2,
        borderWidthSelected: 4
      },
      edges: {
        width: 1,
        color: {
          color: '#cccccc',
          highlight: '#848484',
          hover: '#848484'
        },
        smooth: {
          type: 'continuous',
          forceDirection: 'none',
          roundness: 0.5
        },
        hoverWidth: 2,
        selectionWidth: 2
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 100,
          updateInterval: 50,
          fit: true
        },
        barnesHut: {
          gravitationalConstant: -30000,
          centralGravity: 0.3,
          springLength: 150,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        hideEdgesOnDrag: true,
        hideEdgesOnZoom: true,
        navigationButtons: true,
        keyboard: {
          enabled: true
        }
      }
    };

    network = new vis.Network(container, data, options);

    // Disable physics after stabilization to prevent continuous movement
    network.on("stabilizationIterationsDone", function() {
      network.setOptions({ physics: false });
    });

    // Click handler to navigate to entity pages
    network.on("click", function(params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = data.nodes.find(n => n.id === nodeId);
        if (node) {
          // Extract entity type and create URL
          const type = node.group || node.type || 'people';
          const slug = nodeId.replace(/^(people|organizations|locations|events):/, '').toLowerCase().replace(/\s+/g, '-');
          window.location.href = `entities/${type}/${slug}.md`;
        }
      }
    });

    // Show node info on hover
    network.on("hoverNode", function(params) {
      const nodeId = params.node;
      const node = data.nodes.find(n => n.id === nodeId);
      if (node) {
        network.canvas.body.container.style.cursor = 'pointer';
      }
    });

    network.on("blurNode", function(params) {
      network.canvas.body.container.style.cursor = 'default';
    });
  }

  function fitNetwork() {
    if (network) {
      network.fit({
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuad'
        }
      });
    }
  }

  function filterNodesOnLoad(type, data) {
    currentFilter = type;

    // Filter to people only on initial load
    const filteredNodes = data.nodes.filter(node => {
      const nodeType = node.group || node.type || 'people';
      return nodeType === type;
    });

    const nodeIds = new Set(filteredNodes.map(n => n.id));

    const filteredEdges = data.edges.filter(edge => {
      return nodeIds.has(edge.from) && nodeIds.has(edge.to);
    });

    const filteredData = {
      nodes: filteredNodes,
      edges: filteredEdges
    };

    initNetwork(filteredData);

    // Update info display
    document.getElementById('info').innerHTML = `
      <p><strong>Graph Statistics:</strong></p>
      <ul>
        <li>Currently showing: <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong> (${filteredNodes.length} entities)</li>
        <li>500,000 total relationships in database</li>
        <li>6,607 total entities across all types</li>
        <li><em>Tip: Use "Show All" to see all 500 entities (may be slower)</em></li>
      </ul>
    `;
  }

  function filterNodes(type) {
    if (!allData) return;

    currentFilter = type;
    let filteredData;

    if (type === 'all') {
      filteredData = allData;
    } else {
      // Filter nodes by type
      const filteredNodes = allData.nodes.filter(node => {
        const nodeType = node.group || node.type || 'people';
        return nodeType === type;
      });

      const nodeIds = new Set(filteredNodes.map(n => n.id));

      // Filter edges to only include connections between filtered nodes
      const filteredEdges = allData.edges.filter(edge => {
        return nodeIds.has(edge.from) && nodeIds.has(edge.to);
      });

      filteredData = {
        nodes: filteredNodes,
        edges: filteredEdges
      };
    }

    // Recreate network with filtered data
    network.setData(filteredData);

    // Re-enable physics temporarily for new layout
    network.setOptions({ physics: { enabled: true } });

    // Disable physics after stabilization
    setTimeout(() => {
      network.setOptions({ physics: false });
      fitNetwork();
    }, 2000);

    // Update info display
    const nodeCount = filteredData.nodes.length;
    document.getElementById('info').innerHTML = `
      <p><strong>Graph Statistics:</strong></p>
      <ul>
        <li>Currently showing: <strong>${type === 'all' ? 'All Entities' : type.charAt(0).toUpperCase() + type.slice(1)}</strong> (${nodeCount} entities)</li>
        <li>500,000 total relationships in database</li>
        <li>6,607 total entities across all types</li>
      </ul>
    `;
  }
</script>

<style>
  #network {
    width: 100%;
    height: 800px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    background: #fafafa;
  }

  #controls button {
    margin-right: 10px;
    padding: 8px 16px;
    background: #3399ff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }

  #controls button:hover {
    background: #2277dd;
  }

  #legend ul {
    list-style: none;
    padding: 0;
  }

  #legend li {
    margin: 5px 0;
    font-size: 16px;
  }
</style>

---

## How to Use

- **Zoom:** Mouse wheel or pinch gesture
- **Pan:** Click and drag on empty space
- **Select Node:** Click on a node to navigate to its entity page
- **Hover:** Hover over nodes to highlight connections
- **Filter:** Use buttons above to filter by entity type
- **Fit to Screen:** Reset the view to show all nodes

## Graph Features

This interactive graph visualizes relationships between entities extracted from the Epstein Estate documents:

- **Node Size:** Larger nodes represent entities mentioned more frequently
- **Node Color:** Color indicates entity type (see legend)
- **Edge Width:** Thicker edges indicate stronger relationships (more co-occurrences)
- **Clustering:** Entities that appear together frequently are positioned closer

The graph uses force-directed layout to automatically organize entities based on their relationships. Closely connected entities form clusters, revealing communities and networks within the document collection.

---

*Graph generated from 500,000 entity co-occurrence relationships across 2,897 documents*
