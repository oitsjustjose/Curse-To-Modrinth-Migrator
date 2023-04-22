import React from 'react';
import { Modal } from 'react-bootstrap';

export default ({ show, onHide }) => (
  <Modal
    centered
    show={show}
    onHide={onHide}
  >
    <Modal.Body>
      <div>
        <p>
          This is the splitter between parts of the filename. Many mods use the format
          {' '}
          <code>MODNAME-MCVER-MAJOR.MINOR.PATCH</code>
          , where
          {' '}
          <code>-</code>
          {' '}
          is the delimiter.
        </p>
        <p>
          Using this logic, it is assumed that the Minecraft version for this
          {' '}
          <code>.jar</code>
          -file is between the first and second delimiter, and that the mod version is between
          the second and the end of the file. Formatting aside from this is not supported,
          unfortunately, as I&apos;ve got a bit of trauma
          {' '}
          <sup>(/s)</sup>
          {' '}
          from
          {' '}
          <a href="https://dv2ls.com/code?id=lUY-c4A2H" target="_blank" rel="noreferrer">
            this Regular Expression I wrote.
          </a>
        </p>
      </div>
    </Modal.Body>
  </Modal>
);
