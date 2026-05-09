'use client';

import { useEffect, useState } from 'react';

export function useClientSearchParams(): URLSearchParams {
  const [params, setParams] = useState(() => new URLSearchParams());

  useEffect(() => {
    const update = () => {
      setParams(new URLSearchParams(window.location.search));
    };

    update();
    window.addEventListener('popstate', update);
    return () => window.removeEventListener('popstate', update);
  }, []);

  return params;
}
