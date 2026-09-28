import {
  expect,
  test,
} from "@playwright/test";


const APP_URL =
  process.env.E2E_BASE_URL ||
  "http://127.0.0.1:5173";


const config = {
  donor: [
    process.env.E2E_DONOR_EMAIL,
    process.env.E2E_DONOR_PASSWORD,
  ],

  receiver: [
    process.env.E2E_RECEIVER_EMAIL,
    process.env.E2E_RECEIVER_PASSWORD,
  ],

  volunteer: [
    process.env.E2E_VOLUNTEER_EMAIL,
    process.env.E2E_VOLUNTEER_PASSWORD,
  ],

  admin: [
    process.env.E2E_ADMIN_EMAIL,
    process.env.E2E_ADMIN_PASSWORD,
  ],

  area: process.env.E2E_PICKUP_AREA,
};


function validateConfiguration() {
  for (
    const [role, values]
    of Object.entries(config)
  ) {
    if (
      Array.isArray(values) &&
      values.some((value) => !value)
    ) {
      throw new Error(
        `Set E2E_${role.toUpperCase()}_EMAIL ` +
        `and E2E_${role.toUpperCase()}_PASSWORD.`,
      );
    }
  }

  if (!config.area) {
    throw new Error(
      "Set E2E_PICKUP_AREA to an active " +
      "service-area name.",
    );
  }
}


function localDateTime(minutesFromNow = 0) {
  const date = new Date(
    Date.now() +
    minutesFromNow * 60 * 1000,
  );

  const pad = (value) =>
    String(value).padStart(2, "0");

  return (
    `${date.getFullYear()}-` +
    `${pad(date.getMonth() + 1)}-` +
    `${pad(date.getDate())}T` +
    `${pad(date.getHours())}:` +
    `${pad(date.getMinutes())}`
  );
}


async function signIn(browser, role) {
  const context = await browser.newContext({
    baseURL: APP_URL,
    timezoneId: "Asia/Kolkata",
  });

  const page = await context.newPage();

  await page.goto("/login");

  await page
    .getByLabel("Email address")
    .fill(config[role][0]);

  await page
    .getByLabel("Password")
    .fill(config[role][1]);

  await page
    .getByRole("button", {
      name: "Sign in",
    })
    .click();

  await expect(page).toHaveURL(
    /\/dashboard/,
    {
      timeout: 15000,
    },
  );

  return {
    context,
    page,
  };
}


async function createDonation(
  page,
  {
    foodName,
    quantity = "2",
  },
) {
  await page.goto(
    "/donor/donations/new",
  );

  await expect(
    page.getByRole("heading", {
      name: /Create.*donation/i,
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  await page
    .getByLabel("Food name")
    .fill(foodName);

  const categorySelect =
    page.getByLabel("Food category");

  await expect(
    categorySelect.locator("option"),
  ).not.toHaveCount(1, {
    timeout: 15000,
  });

  await categorySelect.selectOption({
    label: "Prepared Meals",
  });

  await page
    .getByLabel("Quantity")
    .fill(quantity);

  await page
    .getByLabel("Unit")
    .selectOption("PORTION");

  await page
    .getByLabel("Description")
    .fill(
      "Food donation created by the Step 27 " +
      "Playwright end-to-end test.",
    );

  await page
    .getByLabel("Storage condition")
    .fill(
      "Keep covered and collect within the " +
      "configured pickup window.",
    );

  const preparedAt =
    page.getByLabel("Prepared at");

  if (await preparedAt.isEnabled()) {
    await preparedAt.fill(
      localDateTime(-30),
    );
  }

  const useBy =
    page.getByLabel("Use by");

  if (await useBy.isEnabled()) {
    await useBy.fill(
      localDateTime(360),
    );
  }

  await page
    .getByLabel("Pickup area")
    .fill(config.area);

  await page
    .getByLabel("Pickup address")
    .fill(
      `${config.area}, SmartFood E2E pickup point`,
    );

  await page
    .getByLabel("Pickup starts at")
    .fill(localDateTime(30));

  await page
    .getByLabel("Pickup deadline")
    .fill(localDateTime(240));

  await page
    .getByRole("button", {
      name: "Create donation",
    })
    .click();

  await expect(page).toHaveURL(
    /\/donor\/donations\/[0-9a-f-]+$/i,
    {
      timeout: 20000,
    },
  );

  const match = page
    .url()
    .match(
      /\/donor\/donations\/([0-9a-f-]+)$/i,
    );

  if (!match) {
    throw new Error(
      "The donation ID could not be read " +
      "from the current URL.",
    );
  }

  return match[1];
}


async function requestDonation(
  page,
  donationId,
  transportMode,
) {
  await page.goto(
    `/receiver/donations/${donationId}`,
  );

  await expect(
    page.getByRole("heading", {
      name: "Request this donation",
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  await page
    .getByLabel("Message to donor")
    .fill(
      "The receiver can accept this donation " +
      "during the specified pickup window.",
    );

  await page
    .getByLabel("Preferred transport")
    .selectOption(transportMode);

  await page
    .getByRole("button", {
      name: "Submit request",
    })
    .click();

  await expect(
    page.getByText(
      "Your request was submitted successfully.",
    ),
  ).toBeVisible({
    timeout: 15000,
  });
}


async function approveRequest(
  page,
  foodName,
) {
  await page.goto("/donor/requests");

  const requestCard =
    page
      .locator("article")
      .filter({
        hasText: foodName,
      })
      .first();

  await expect(requestCard).toBeVisible({
    timeout: 15000,
  });

  await requestCard
    .getByRole("button", {
      name: "Approve request",
    })
    .click();

  const dialog =
    page.getByRole("dialog");

  await expect(dialog).toBeVisible();

  const optionalNote =
    dialog.getByLabel(
      "Decision note (optional)",
    );

  if (await optionalNote.isVisible()) {
    await optionalNote.fill(
      "Approved by the Step 27 UI test.",
    );
  }

  await dialog
    .getByRole("button", {
      name: "Confirm approval",
    })
    .click();

  await expect(
    page.getByText(
      /request was approved successfully/i,
    ),
  ).toBeVisible({
    timeout: 15000,
  });
}


async function generateRecommendations(
  page,
  donationId,
) {
  await page.goto(
    (
      `/donor/donations/${donationId}` +
      "/recommendations"
    ),
  );

  await expect(
    page.getByRole("heading", {
      name: "Recommended receivers",
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  const generateButton =
    page.getByRole("button", {
      name:
        /Generate ranking|Refresh ranking/,
    });

  await generateButton.click();

  await expect(
    page.getByText(/Model:/),
  ).toBeVisible({
    timeout: 30000,
  });
}


async function confirmDirectHandover(
  page,
  donationId,
) {
  await page.goto(
    `/fulfilment/${donationId}`,
  );

  await expect(
    page.getByRole("heading", {
      name: "Confirm food handover",
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  await page
    .getByLabel(
      /Actual handover quantity/i,
    )
    .fill("2");

  await page
    .getByLabel("Notes")
    .fill(
      "Direct collection completed successfully.",
    );

  await page
    .getByRole("button", {
      name: "Confirm handover",
    })
    .click();

  await expect(
    page.getByText(
      "Food handover was confirmed successfully.",
    ),
  ).toBeVisible({
    timeout: 15000,
  });
}


async function confirmDirectReceiverReceipt(
  page,
  donationId,
) {
  await page.goto(
    `/fulfilment/${donationId}`,
  );

  await expect(
    page.getByRole("heading", {
      name: "Confirm food receipt",
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  await page
    .getByLabel(/Accepted quantity/i)
    .fill("2");

  await page
    .getByLabel("Receipt result")
    .selectOption("NONE");

  await page
    .getByRole("button", {
      name: "Confirm receipt",
    })
    .click();

  await expect(
    page.getByText(
      /Receipt was confirmed successfully/i,
    ),
  ).toBeVisible({
    timeout: 15000,
  });
}


async function confirmVolunteerReceipt(
  page,
  donationId,
) {
  await page.goto(
    `/receiver/receipts/${donationId}`,
  );

  await expect(
    page.getByRole("heading", {
      name: "Confirm receipt",
    }),
  ).toBeVisible({
    timeout: 15000,
  });

  await page
    .getByLabel("Accepted quantity")
    .fill("2");

  await page
    .getByLabel("Unit")
    .selectOption("PORTION");

  await page
    .getByLabel(
      "Discrepancy",
      {
        exact: true,
      },
    )
    .selectOption("NONE");

  await page
    .getByRole("button", {
      name: "Confirm receipt",
    })
    .click();

  await expect(page).toHaveURL(
    /\/receiver\/requests\/?$/,
    {
      timeout: 15000,
    },
  );
}


test.beforeAll(() => {
  validateConfiguration();
});


test.describe.configure({
  mode: "serial",
});


test.setTimeout(120000);


test(
  (
    "donor creates; receiver requests; donor " +
    "approves; direct collection, recommendations " +
    "and impact"
  ),
  async ({ browser }) => {
    const foodName =
      `Step 27 direct meals ${Date.now()}`;

    const donor = await signIn(
      browser,
      "donor",
    );

    const donationId =
      await createDonation(
        donor.page,
        {
          foodName,
          quantity: "2",
        },
      );

    await generateRecommendations(
      donor.page,
      donationId,
    );

    await donor.context.close();

    const receiver = await signIn(
      browser,
      "receiver",
    );

    await requestDonation(
      receiver.page,
      donationId,
      "RECEIVER_COLLECTION",
    );

    await receiver.context.close();

    const donorApproval = await signIn(
      browser,
      "donor",
    );

    await approveRequest(
      donorApproval.page,
      foodName,
    );

    await confirmDirectHandover(
      donorApproval.page,
      donationId,
    );

    await donorApproval.context.close();

    const receiverReceipt =
      await signIn(
        browser,
        "receiver",
      );

    await confirmDirectReceiverReceipt(
      receiverReceipt.page,
      donationId,
    );

    await receiverReceipt.page.goto(
      "/analytics",
    );

    await expect(
      receiverReceipt.page.getByRole(
        "heading",
        {
          name: "Impact dashboard",
        },
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await expect(
      receiverReceipt.page.getByRole(
        "heading",
        {
          name:
            "Confirmed quantity redistributed",
        },
      ),
    ).toBeVisible();

    await expect(
      receiverReceipt.page.getByText(
        "No completed receipt-confirmed quantities yet.",
      ),
    ).toHaveCount(0);

    await receiverReceipt.context.close();
  },
);


test(
  (
    "volunteer delivery requires a receiver receipt"
  ),
  async ({ browser }) => {
    const foodName =
      `Step 27 volunteer meals ${Date.now()}`;

    const donor = await signIn(
      browser,
      "donor",
    );

    const donationId =
      await createDonation(
        donor.page,
        {
          foodName,
          quantity: "2",
        },
      );

    await donor.context.close();

    const receiver = await signIn(
      browser,
      "receiver",
    );

    await requestDonation(
      receiver.page,
      donationId,
      "VOLUNTEER_DELIVERY",
    );

    await receiver.context.close();

    const donorApproval = await signIn(
      browser,
      "donor",
    );

    await approveRequest(
      donorApproval.page,
      foodName,
    );

    await donorApproval.context.close();

    const volunteer = await signIn(
      browser,
      "volunteer",
    );

    await volunteer.page.goto(
      "/volunteer/tasks",
    );

    const taskCard =
      volunteer.page
        .locator("article")
        .filter({
          hasText: foodName,
        })
        .first();

    await expect(taskCard).toBeVisible({
      timeout: 20000,
    });

    await taskCard
      .getByRole("button", {
        name: "Accept task",
      })
      .click();

    await expect(
      volunteer.page,
    ).toHaveURL(
      /\/volunteer\/tasks\/[0-9a-f-]+$/i,
      {
        timeout: 15000,
      },
    );

    await volunteer.page
      .getByRole("button", {
        name: "I arrived at the donor",
      })
      .click();

    await expect(
      volunteer.page.getByRole(
        "button",
        {
          name: "Record food pickup",
        },
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await volunteer.page
      .getByRole("button", {
        name: "Record food pickup",
      })
      .click();

    let dialog =
      volunteer.page.getByRole("dialog");

    await dialog
      .getByLabel(/Actual quantity/i)
      .fill("2");

    await dialog
      .getByLabel("Notes")
      .fill(
        "Food collected from the donor.",
      );

    await dialog
      .getByRole("button", {
        name: "Confirm pickup",
      })
      .click();

    await expect(
      volunteer.page.getByRole(
        "button",
        {
          name: "I arrived at the receiver",
        },
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await volunteer.page
      .getByRole("button", {
        name: "I arrived at the receiver",
      })
      .click();

    await expect(
      volunteer.page.getByRole(
        "button",
        {
          name: "Record delivery",
        },
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await volunteer.page
      .getByRole("button", {
        name: "Record delivery",
      })
      .click();

    dialog =
      volunteer.page.getByRole("dialog");

    await dialog
      .getByLabel(/Actual quantity/i)
      .fill("2");

    await dialog
      .getByLabel("Notes")
      .fill(
        "Food delivered to the receiver.",
      );

    await dialog
      .getByRole("button", {
        name: "Confirm delivery",
      })
      .click();

    await expect(
      volunteer.page.getByText(
        "Waiting for receiver",
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await volunteer.context.close();

    const receiverReceipt =
      await signIn(
        browser,
        "receiver",
      );

    await confirmVolunteerReceipt(
      receiverReceipt.page,
      donationId,
    );

    await receiverReceipt.context.close();

    const volunteerCompleted =
      await signIn(
        browser,
        "volunteer",
      );

    await volunteerCompleted.page.goto(
      "/volunteer/history",
    );

    await expect(
      volunteerCompleted.page
        .getByText(foodName)
        .first(),
    ).toBeVisible({
      timeout: 15000,
    });

    await volunteerCompleted.context.close();
  },
);


test(
  (
    "complaint submission and admin review " +
    "through the UI"
  ),
  async ({ browser }) => {
    const foodName =
      `Step 27 complaint donation ${Date.now()}`;

    const complaintDescription =
      (
        "Step 27 automated complaint: verify " +
        `administrative review ${Date.now()}.`
      );

    const donor = await signIn(
      browser,
      "donor",
    );

    const donationId =
      await createDonation(
        donor.page,
        {
          foodName,
          quantity: "2",
        },
      );

    /*
     * Supplying donationId through the query string
     * automatically opens the complaint dialog and
     * pre-populates the donation ID.
     */
    await donor.page.goto(
      (
        "/complaints?donationId=" +
        encodeURIComponent(donationId)
      ),
    );

    const complaintDialog =
      donor.page.getByRole("dialog");

    await expect(
      complaintDialog,
    ).toBeVisible({
      timeout: 15000,
    });

    const donationIdInput =
      complaintDialog.getByLabel(
        "Donation ID",
      );

    await expect(
      donationIdInput,
    ).toHaveValue(donationId);

    const descriptionInput =
      complaintDialog.getByLabel(
        "Describe the problem",
      );

    await descriptionInput.fill(
      complaintDescription,
    );

    await expect(
      descriptionInput,
    ).toHaveValue(
      complaintDescription,
    );

    const submitComplaintButton =
      complaintDialog.getByRole(
        "button",
        {
          name: "Submit complaint",
        },
      );

    await expect(
      submitComplaintButton,
    ).toBeEnabled({
      timeout: 10000,
    });

    await submitComplaintButton.click();

    await expect(
      donor.page.getByText(
        "Your complaint was submitted successfully.",
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await donor.context.close();

    const admin = await signIn(
      browser,
      "admin",
    );

    await admin.page.goto(
      "/admin/complaints",
    );

    const complaintCard = () =>
      admin.page
        .locator("article")
        .filter({
          hasText: complaintDescription,
        })
        .first();

    await expect(
      complaintCard(),
    ).toBeVisible({
      timeout: 15000,
    });

    await complaintCard()
      .getByRole("button", {
        name: "Start review",
      })
      .click();

    await expect(
      admin.page.getByText(
        /Complaint review started successfully/i,
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    /*
     * The complaint leaves the default OPEN filter after
     * review begins, so show every status.
     */
    const statusSelect =
      admin.page.locator("select").first();

    await statusSelect.selectOption("ALL");

    await expect(
      complaintCard(),
    ).toBeVisible({
      timeout: 15000,
    });

    await complaintCard()
      .getByRole("button", {
        name: "Resolve complaint",
      })
      .click();

    const resolutionDialog =
      admin.page.getByRole("dialog");

    await expect(
      resolutionDialog,
    ).toBeVisible();

    await resolutionDialog
      .getByLabel(
        "Resolution explanation",
      )
      .fill(
        "The complaint was reviewed and resolved " +
        "during the Step 27 UI test.",
      );

    await resolutionDialog
      .getByRole("button", {
        name: "Confirm resolution",
      })
      .click();

    await expect(
      admin.page.getByText(
        /Complaint resolved successfully/i,
      ),
    ).toBeVisible({
      timeout: 15000,
    });

    await admin.context.close();
  },
);