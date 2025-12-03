import { useEffect, useRef, useState } from "react";
import { Button, Stack, Typography } from "@mui/material";

function TerraExplorerControls({ selectedImage }) {
  const sgWorldRef = useRef(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let cancelled = false;

    function waitForFusion() {
      try {
        const parentWin = window.parent || window;

        if (
          parentWin &&
          typeof parentWin.SGWorld !== "undefined" &&
          parentWin.SGWorld &&
          parentWin.SGWorld.Creator
        ) {
          sgWorldRef.current = parentWin.SGWorld;
          setConnected(true);
          console.log("✅ Connected to Fusion SGWorld");
          return;
        }
      } catch (err) {
        console.warn("Error accessing parent.SGWorld:", err);
      }

      if (!cancelled) {
        setTimeout(waitForFusion, 200);
      }
    }

    waitForFusion();

    return () => {
      cancelled = true;
    };
  }, []);

  const flyToAltitude = () => {
    const SGWorld = sgWorldRef.current;
    if (!SGWorld) {
      console.warn("SGWorld not initialised yet");
      return;
    }

    const pos = SGWorld.Navigate.GetPosition();
    pos.Altitude = 1000;
    SGWorld.Navigate.FlyTo(pos, 0);
  };

  const flyToSelectedImage = () => {
    const SGWorld = sgWorldRef.current;
    if (!SGWorld || !selectedImage) {
      console.warn("No SGWorld or selectedImage");
      return;
    }

    // Example: WGS84 lon/lat from your image, alt from alt_m
    const lon = selectedImage.lon;
    const lat = selectedImage.lat;
    const alt = selectedImage.alt_m || 100;

    // You may need to adjust AltitudeType and angles depending on TE version
    const ALTITUDE_TYPE = 3; // check TE docs (e.g. 1=AT_ABSOLUTE, 3=AT_TERRAIN_RELATIVE, etc.)

    const pos = SGWorld.Creator.CreatePosition(
      lon,
      lat,
      alt,
      ALTITUDE_TYPE,
      selectedImage.yaw_deg || 0, // yaw/heading
      -30,                        // pitch
      0,                          // roll
      0                           // distance; 0 = exact position
    );

    SGWorld.Navigate.FlyTo(pos, 0);
  };

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Typography variant="caption" sx={{ opacity: 0.7 }}>
        {connected ? "TerraExplorer: Connected" : "TerraExplorer: Connecting..."}
      </Typography>

      <Button
        variant="outlined"
        size="small"
        onClick={flyToAltitude}
        disabled={!connected}
      >
        Fly to 1000m
      </Button>

      <Button
        variant="contained"
        size="small"
        disabled={!connected || !selectedImage}
        onClick={flyToSelectedImage}
      >
        Fly to image
      </Button>
    </Stack>
  );
}

export default TerraExplorerControls;

