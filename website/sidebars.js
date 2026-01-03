/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'deployment',
        'quickstart',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture',
        'agents',
        'database',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api',
        'websocket',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      items: [
        'mcp',
        'dapr',
        'kafka',
      ],
    },
  ],
};

export default sidebars;
