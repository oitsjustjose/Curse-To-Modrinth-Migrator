import React, { useState, useEffect } from 'react';

export default ({ id }) => {
  const [logs, setLogs] = useState('');

  useEffect(() => {
    const handle = setInterval(async () => {
      const resp = await fetch(`/api/v1/jobs/${id}`, { method: 'POST' });
      if (resp.status < 500) {
        setLogs(await resp.text());
      } else {
        setLogs(`${resp.status}: ${resp.statusText}`);
      }
    }, 500);
    return () => clearInterval(handle);
  }, [setLogs, id]);

  return (
    <code>
      {logs.split('\n').map((log) => (
        <p>{log}</p>
      ))}
    </code>
  );
};
