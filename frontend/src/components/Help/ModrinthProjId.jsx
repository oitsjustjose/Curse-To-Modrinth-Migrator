import React from 'react';
import { Image, Modal } from 'react-bootstrap';
import Example from '../../img/mpjid.png';

export default ({ show, onHide }) => (
  <Modal
    centered
    show={show}
    onHide={onHide}
  >
    <Modal.Header closeButton>
      <h4>Modrinth Project IDs and You</h4>
    </Modal.Header>
    <Modal.Body>
      <div>
        <p>
          Your Modrinth Project ID is *not* the same as the Slug/Name.
          It can instead be found in the sidebar of your project
          (even if your project is still pending approval), like so:
          {' '}
          <Image
            className="d-block m-auto p-5"
            src={Example}
            rounded
          />
        </p>
      </div>
    </Modal.Body>
  </Modal>
);
