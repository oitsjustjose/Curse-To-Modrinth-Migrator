import React, { useState } from 'react';
import { Modal, Image, Button } from 'react-bootstrap';
import ThirdPartyHelp from '../../img/cftpd.png';
import { DoModrinthOauth } from '../../shared';

export default ({ dark, override, propagateOnHide }) => {
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
            The CurseForge Slug for your Mod. This can be found in the General Settings for your
            project page
          </li>
          <li>
            The Modrinth Project ID. This can be found in the side panel of your Modrinth project
          </li>
        </ul>

        <p>
          This tool works fastest if your CurseForge Project allows Third Party Downloads. If you
          do, migration should take about 1 minute for every 50 files. If you do not, migration
          takes 7 minutes due to nasty workarounds I had to implement. I suggest enabling third
          party downloads in your project settings:
        </p>

        <Image
          style={{ filter: dark ? 'invert(1)' : 'none' }}
          src={ThirdPartyHelp}
          className="d-block mx-auto my-3 mw-100"
          rounded
        />

        <p>
          While you wait for your migration to complete, you can close this tab,
          put it in the background, or
        </p>
        <ul>
          <li>
            Support me
            {' '}
            <a href="https://dv2ls.com/don8" target="_blank" rel="noreferrer">with a Donation</a>
          </li>
          <li>Share this tool on Twitter, Discord or whatever you please! </li>
        </ul>

        <div className="w-100 d-flex justify-content-center align-items-center">
          <Button variant="success" className="modrinth" onClick={DoModrinthOauth}>
            Authenticate with Modrinth
          </Button>
        </div>
      </Modal.Body>
    </Modal>
  );
};
