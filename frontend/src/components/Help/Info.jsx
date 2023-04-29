import React, { useState } from 'react';
import { Modal } from 'react-bootstrap';

export default ({ override, propagateOnHide }) => {
  const [show, setShow] = useState(!window.localStorage.getItem('info-dismissed'));

  const onHide = () => {
    window.localStorage.setItem('info-dismissed', true);
    setShow(false);
    propagateOnHide();
  };

  return (
    <Modal
      centered
      size="lg"
      show={override || show}
      onHide={onHide}
    >
      <Modal.Header closeButton>
        <Modal.Title>CurseForge to Modrinth Mod Migrator (CTMMM)</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>
          <b>Welcome!</b>
          {' '}
          In order to use this tool you&apos;ll need to have already created (if it&apos;s
          still &quot;Under Review&quot;, that&apos;s ok) your Modrinth Page, and a few
          other things:
        </p>

        <ul>
          <li>
            A
            {' '}
            <a href="https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token" target="_blank" rel="noreferrer">
              GitHub Personal Access Token
            </a>
            {' '}
            for the Account you used to log into Modrinth. No
            permissions need to be granted to the PAT, this token will be encrypted from end
            to end (even in storage), and it will only be used for requests to Modrinth
            (feel encouraged to browse this source code to verify).
          </li>
          <li>
            The CurseForge Slug for your Mod. This can be found in the General Settings for your
            project page
          </li>
          <li>
            The Modrinth Project ID. This can be found in the side panel of your Modrinth project
          </li>
        </ul>

        <p>
          This tool works on a queue-based system since this process is pretty slow.
          I apologize that it might take a while to process, but while you wait you can always:
        </p>

        <ul>
          <li>
            Support me
            {' '}
            <a href="https://dv2ls.com/don8" target="_blank" rel="noreferrer">with a Donation</a>
          </li>
          <li>Share this tool on Social Media!</li>
        </ul>
      </Modal.Body>
    </Modal>
  );
};
