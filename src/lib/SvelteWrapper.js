import React, { useRef, useEffect } from 'react';
import { render } from 'svelte';
import ThreeDVisualizer from './ThreeDVisualizer.svelte';

const SvelteWrapper = (props) => {
  const containerRef = useRef(null);

  useEffect(() => {
    const { current } = containerRef;
    const svelteComponent = new ThreeDVisualizer({
      target: current,
      props,
    });

    return () => {
      svelteComponent.$destroy();
    };
  }, [props]);

  return <div ref={containerRef} />;
};

export default SvelteWrapper;
